"""
Management command para popular o banco de dados com dados de teste usando Faker.

Cria a hierarquia: HomePage → Canais → Conteúdos (vídeo, áudio, documento, apresentação).

Uso:
    python manage.py popular_banco                    # Com confirmação interativa
    python manage.py popular_banco --forcereset       # Sem confirmação (apaga dados de teste)
    python manage.py popular_banco --canais 5 --conteudos-por-canal 10  # Personalizado
"""
import logging
import sys
from typing import Optional

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from faker import Faker
from wagtail.models import Page, Site

from home.models import HomePage
from canais.models import CanalPage
from conteudos.models import (
    ConteudoPage,
    Tipo,
    Licenca,
    CategoriaConteudo,
)
from curriculo.models import (
    NivelEnsino,
    CurricularComponentCategory,
    CurricularComponent,
)
from series.models import Serie, Temporada
from usuarios.models import Role

User = get_user_model()

logger = logging.getLogger(__name__)

# Constantes para configuração padrão
DEFAULT_CANAIS = 4
DEFAULT_CONTEUDOS_POR_CANAL = 8
DEFAULT_TIPOS_SLUGS = ["video", "audio", "documento", "apresentacao"]
DEFAULT_LICENCAS = [
    {"slug": "cc-by", "name": "CC BY 4.0", "description": "Creative Commons Atribuição 4.0 Internacional"},
    {"slug": "cc-by-sa", "name": "CC BY-SA 4.0", "description": "Creative Commons Atribuição-CompartilhaIgual 4.0 Internacional"},
    {"slug": "cc-by-nc", "name": "CC BY-NC 4.0", "description": "Creative Commons Atribuição-NãoComercial 4.0 Internacional"},
    {"slug": "public-domain", "name": "Domínio Público", "description": "Obra em domínio público"},
]
DEFAULT_NIVEIS_ENSINO = [
    {"name": "1º ano do Ensino Fundamental", "slug": "1ano-ef", "ordem": 1},
    {"name": "2º ano do Ensino Fundamental", "slug": "2ano-ef", "ordem": 2},
    {"name": "3º ano do Ensino Fundamental", "slug": "3ano-ef", "ordem": 3},
    {"name": "4º ano do Ensino Fundamental", "slug": "4ano-ef", "ordem": 4},
    {"name": "5º ano do Ensino Fundamental", "slug": "5ano-ef", "ordem": 5},
    {"name": "6º ano do Ensino Fundamental", "slug": "6ano-ef", "ordem": 6},
    {"name": "7º ano do Ensino Fundamental", "slug": "7ano-ef", "ordem": 7},
    {"name": "8º ano do Ensino Fundamental", "slug": "8ano-ef", "ordem": 8},
    {"name": "9º ano do Ensino Fundamental", "slug": "9ano-ef", "ordem": 9},
    {"name": "1º ano do Ensino Médio", "slug": "1ano-em", "ordem": 10},
    {"name": "2º ano do Ensino Médio", "slug": "2ano-em", "ordem": 11},
    {"name": "3º ano do Ensino Médio", "slug": "3ano-em", "ordem": 12},
]
DEFAULT_CATEGORIAS_COMPONENTE = [
    {"name": "Linguagens", "slug": "linguagens", "ordem": 1},
    {"name": "Matemática", "slug": "matematica", "ordem": 2},
    {"name": "Ciências da Natureza", "slug": "ciencias-natureza", "ordem": 3},
    {"name": "Ciências Humanas", "slug": "ciencias-humanas", "ordem": 4},
    {"name": "Artes", "slug": "artes", "ordem": 5},
    {"name": "Educação Física", "slug": "educacao-fisica", "ordem": 6},
]
DEFAULT_CANAIS_NOMES = [
    "TV Anísio Teixeira",
    "Rádio Anísio Teixeira",
    "EMITEC",
    "Recursos Educacionais Abertos",
    "Projetos Artísticos",
    "Formação Continuada",
]


class Command(BaseCommand):
    """Comando para popular o banco com dados de teste realistas."""

    help = "Popula o banco com hierarquia Home → Canais → Conteúdos usando Faker (pt_BR)."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fake = Faker("pt_BR")
        self.stats = {
            "canais_criados": 0,
            "conteudos_criados": 0,
            "tipos_criados": 0,
            "licencas_criadas": 0,
            "categorias_criadas": 0,
            "componentes_criados": 0,
        }

    def add_arguments(self, parser):
        parser.add_argument(
            "--forcereset",
            action="store_true",
            help="Apaga dados de teste existentes sem confirmação interativa.",
        )
        parser.add_argument(
            "--canais",
            type=int,
            default=DEFAULT_CANAIS,
            help=f"Número de canais a criar (padrão: {DEFAULT_CANAIS}).",
        )
        parser.add_argument(
            "--conteudos-por-canal",
            type=int,
            default=DEFAULT_CONTEUDOS_POR_CANAL,
            help=f"Número de conteúdos por canal (padrão: {DEFAULT_CONTEUDOS_POR_CANAL}).",
        )
        parser.add_argument(
            "--skip-curriculo",
            action="store_true",
            help="Pula criação de níveis, categorias e componentes curriculares.",
        )

    def _confirm_reset(self) -> bool:
        """Solicita confirmação antes de apagar dados."""
        self.stdout.write(self.style.WARNING(
            "\n⚠️  ATENÇÃO: Esta operação irá APAGAR todas as páginas de canais, "
            "conteúdos, tipos, licenças e categorias de conteúdo existentes.\n"
            "A HomePage será preservada (recriada se não existir).\n"
        ))
        confirm = input("Tem certeza que deseja continuar? [s/N]: ").strip().lower()
        return confirm in ("s", "sim", "y", "yes")

    def _get_or_create_homepage(self) -> HomePage:
        """Obtém ou cria a HomePage na raiz do site."""
        # Tenta encontrar HomePage existente na raiz (depth=2)
        homepage = HomePage.objects.filter(depth=2).first()

        if homepage:
            self.stdout.write(f"✓ HomePage existente encontrada: {homepage.title} (id={homepage.id})")
            return homepage

        # Cria nova HomePage como filha da raiz (root page)
        root = Page.get_first_root_node()
        if not root:
            raise CommandError("Nenhuma página raiz encontrada. Execute migrate primeiro.")

        homepage = HomePage(
            title="Nova PAT - Portal de Aprendizagem",
            slug="home",
            draft_title="Nova PAT - Portal de Aprendizagem",
        )
        root.add_child(instance=homepage)
        homepage.save_revision().publish()

        # Garante que o Site aponte para esta homepage
        site = Site.objects.filter(is_default_site=True).first()
        if site:
            site.root_page = homepage
            site.save()
        else:
            Site.objects.create(hostname="localhost", root_page=homepage, is_default_site=True)

        self.stdout.write(self.style.SUCCESS(f"✓ HomePage criada: {homepage.title} (id={homepage.id})"))
        return homepage

    def _limpar_dados_teste(self, forcereset: bool) -> None:
        """Remove dados de teste de forma segura."""
        if not forcereset and not self._confirm_reset():
            raise CommandError("Operação cancelada pelo usuário.")

        self.stdout.write(self.style.WARNING("\n🗑️  Limpando dados de teste existentes..."))

        # Apaga em ordem reversa de dependência (filhos antes dos pais)
        # Serie e Temporada (filhos de root, pais de ConteudoPage)
        Temporada.objects.all().delete()
        self.stdout.write("  ✓ Temporada removidos")
        Serie.objects.all().delete()
        self.stdout.write("  ✓ Serie removidos")

        # ConteudoPage (filhos de CanalPage ou Temporada)
        ConteudoPage.objects.all().delete()
        self.stdout.write("  ✓ ConteudoPage removidos")

        # CategoriaConteudo (depende de CanalPage) - precisa apagar filhos antes dos pais
        # devido ao FK parent com PROTECT
        while CategoriaConteudo.objects.exists():
            # Apaga categorias que não têm filhos (folhas) primeiro
            folhas = CategoriaConteudo.objects.filter(subcategorias__isnull=True)
            if not folhas.exists():
                # Se não há folhas, força exclusão de todas (caso de ciclos ou dados órfãos)
                CategoriaConteudo.objects.all().delete()
                break
            folhas.delete()
        self.stdout.write("  ✓ CategoriaConteudo removidos")

        # CanalPage (filhos de HomePage/root)
        CanalPage.objects.all().delete()
        self.stdout.write("  ✓ CanalPage removidos")

        # Tipos, Licenças (snippets)
        Tipo.objects.all().delete()
        self.stdout.write("  ✓ Tipo removidos")

        Licenca.objects.all().delete()
        self.stdout.write("  ✓ Licenca removidos")

        # Dados curriculares (opcional)
        CurricularComponent.objects.all().delete()
        CurricularComponentCategory.objects.all().delete()
        NivelEnsino.objects.all().delete()
        self.stdout.write("  ✓ Dados curriculares removidos")

        # Usuários de teste (mantém superusers)
        User.objects.filter(is_superuser=False).delete()
        self.stdout.write("  ✓ Usuários de teste removidos")

        self.stdout.write(self.style.SUCCESS("✓ Limpeza concluída.\n"))

    def _criar_tipos(self) -> list[Tipo]:
        """Cria os tipos de conteúdo com slugs conhecidos para templates."""
        self.stdout.write("📦 Criando tipos de conteúdo...")

        tipos_config = [
            {
                "slug": "video",
                "name": "Vídeo",
                "description": "Conteúdo em formato de vídeo (aulas, documentários, animações).",
                "formatos": ["mp4", "webm", "ogg", "mov"],
                "ordem": 1,
            },
            {
                "slug": "audio",
                "name": "Áudio",
                "description": "Conteúdo em formato de áudio (podcasts, audiolivros, músicas).",
                "formatos": ["mp3", "wav", "ogg", "flac"],
                "ordem": 2,
            },
            {
                "slug": "documento",
                "name": "Documento",
                "description": "Documentos textuais (PDFs, apostilas, artigos, relatórios).",
                "formatos": ["pdf", "docx", "odt", "txt", "rtf"],
                "ordem": 3,
            },
            {
                "slug": "apresentacao",
                "name": "Apresentação",
                "description": "Apresentações de slides (PowerPoint, Impress, Google Slides).",
                "formatos": ["pptx", "odp", "pdf"],
                "ordem": 4,
            },
        ]

        tipos = []
        for config in tipos_config:
            tipo, created = Tipo.objects.get_or_create(
                slug=config["slug"],
                defaults={
                    "name": config["name"],
                    "description": config["description"],
                    "options": {"formatos": config["formatos"]},
                    "is_active": True,
                    "ordem": config["ordem"],
                },
            )
            if created:
                self.stats["tipos_criados"] += 1
                self.stdout.write(f"  ✓ Tipo criado: {tipo.name} (slug={tipo.slug})")
            else:
                self.stdout.write(f"  ○ Tipo já existe: {tipo.name} (slug={tipo.slug})")
            tipos.append(tipo)

        return tipos

    def _criar_licencas(self) -> list[Licenca]:
        """Cria licenças padrão."""
        self.stdout.write("📄 Criando licenças...")

        licencas = []
        for i, config in enumerate(DEFAULT_LICENCAS):
            licenca, created = Licenca.objects.get_or_create(
                slug=config["slug"],
                defaults={
                    "name": config["name"],
                    "description": config["description"],
                    "url": f"https://creativecommons.org/licenses/{config['slug'].replace('cc-', '')}/4.0/",
                    "is_active": True,
                    "ordem": i + 1,
                },
            )
            if created:
                self.stats["licencas_criadas"] += 1
                self.stdout.write(f"  ✓ Licença criada: {licenca.name}")
            else:
                self.stdout.write(f"  ○ Licença já existe: {licenca.name}")
            licencas.append(licenca)

        return licencas

    def _criar_dados_curriculares(self) -> tuple[list[NivelEnsino], list[CurricularComponentCategory], list[CurricularComponent]]:
        """Cria níveis de ensino, categorias e componentes curriculares."""
        self.stdout.write("🎓 Criando dados curriculares...")

        # Níveis de ensino
        niveis = []
        for config in DEFAULT_NIVEIS_ENSINO:
            nivel, created = NivelEnsino.objects.get_or_create(
                slug=config["slug"],
                defaults={
                    "name": config["name"],
                    "ordem": config["ordem"],
                    "is_active": True,
                },
            )
            if created:
                self.stdout.write(f"  ✓ Nível criado: {nivel.name}")
            niveis.append(nivel)

        # Categorias de componente
        categorias = []
        for config in DEFAULT_CATEGORIAS_COMPONENTE:
            cat, created = CurricularComponentCategory.objects.get_or_create(
                slug=config["slug"],
                defaults={
                    "name": config["name"],
                    "ordem": config["ordem"],
                    "is_active": True,
                },
            )
            if created:
                self.stdout.write(f"  ✓ Categoria criada: {cat.name}")
            categorias.append(cat)

        # Componentes curriculares (combinação nível + categoria)
        componentes = []
        for nivel in niveis:
            for cat in categorias:
                # Nome do componente varia por nível
                if "Fundamental" in nivel.name:
                    ano = nivel.name.split("º")[0]
                    nome_base = f"{cat.name} — {ano}º ano"
                else:
                    ano = nivel.name.split("º")[0]
                    nome_base = f"{cat.name} — {ano}º ano"

                comp, created = CurricularComponent.objects.get_or_create(
                    name=nome_base,
                    nivel=nivel,
                    category=cat,
                    defaults={
                        "slug": f"{cat.slug}-{nivel.slug}",
                        "description": f"Componente de {cat.name.lower()} para {nivel.name.lower()}.",
                        "ordem": cat.ordem,
                        "is_active": True,
                    },
                )
                if created:
                    self.stats["componentes_criados"] += 1
                componentes.append(comp)

        self.stdout.write(f"  ✓ {len(componentes)} componentes curriculares criados/verificados")
        return niveis, categorias, componentes

    def _criar_usuario_autor(self) -> User:
        """Cria ou obtém um usuário autor para os conteúdos."""
        # Tenta pegar um superuser existente
        autor = User.objects.filter(is_superuser=True).first()

        if autor:
            self.stdout.write(f"✓ Usando superuser existente como autor: {autor.username}")
            return autor

        # Cria usuário autor padrão
        role_default = Role.get_default_role()
        autor = User.objects.create_user(
            username="autor_teste",
            email="autor@teste.local",
            password="senha123",
            first_name="Autor",
            last_name="Teste",
            role=role_default,
            verified=True,
            is_staff=True,
        )
        self.stdout.write(self.style.SUCCESS(f"✓ Usuário autor criado: {autor.username}"))
        return autor

    def _criar_canais(self, homepage: HomePage, qtd: int) -> list[CanalPage]:
        """Cria canais como filhos da HomePage."""
        self.stdout.write(f"📺 Criando {qtd} canais...")

        canais = []
        nomes_usados = set()

        for i in range(qtd):
            # Usa nomes pré-definidos ou gera com Faker
            if i < len(DEFAULT_CANAIS_NOMES):
                nome_base = DEFAULT_CANAIS_NOMES[i]
            else:
                nome_base = self.fake.unique.company()

            # Garante nome único
            nome = nome_base
            contador = 1
            while nome in nomes_usados or CanalPage.objects.filter(name=nome).exists():
                contador += 1
                nome = f"{nome_base} {contador}"
            nomes_usados.add(nome)

            # Gera slug único
            slug_base = nome.lower().replace(" ", "-").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ç", "c")
            slug = slug_base
            contador_slug = 1
            while CanalPage.objects.filter(slug=slug).exists():
                contador_slug += 1
                slug = f"{slug_base}-{contador_slug}"

            canal = CanalPage(
                title=nome,
                name=nome,
                slug=slug,
                description=self.fake.paragraph(nb_sentences=3),
                is_active=True,
                options={"cor": self.fake.hex_color()},
            )

            homepage.add_child(instance=canal)
            canal.save_revision().publish()

            self.stats["canais_criados"] += 1
            canais.append(canal)
            self.stdout.write(f"  ✓ Canal criado: {canal.name} (slug={canal.slug})")

        return canais

    def _criar_categorias_por_canal(self, canais: list[CanalPage]) -> dict[int, list[CategoriaConteudo]]:
        """Cria categorias de conteúdo para cada canal."""
        self.stdout.write("📂 Criando categorias por canal...")

        categorias_por_canal = {}

        for canal in canais:
            qtd_categorias = self.fake.random_int(min=3, max=6)
            categorias = []

            for i in range(qtd_categorias):
                nome = self.fake.unique.word().capitalize() + " " + self.fake.word().capitalize()
                slug_base = nome.lower().replace(" ", "-")
                slug = slug_base
                contador = 1
                while CategoriaConteudo.objects.filter(slug=slug, canal=canal).exists():
                    contador += 1
                    slug = f"{slug_base}-{contador}"

                # 30% chance de ter categoria pai
                parent = None
                if categorias and self.fake.random_int(1, 100) <= 30:
                    parent = self.fake.random_element(categorias)

                categoria = CategoriaConteudo.objects.create(
                    name=nome,
                    slug=slug,
                    description=self.fake.sentence(),
                    canal=canal,
                    parent=parent,
                    is_active=True,
                    ordem=i + 1,
                )
                self.stats["categorias_criadas"] += 1
                categorias.append(categoria)
                self.stdout.write(f"    ✓ Categoria: {categoria.name} (canal={canal.name})")

            categorias_por_canal[canal.id] = categorias

        return categorias_por_canal

    def _criar_conteudos(
        self,
        canais: list[CanalPage],
        tipos: list[Tipo],
        licencas: list[Licenca],
        categorias_por_canal: dict[int, list[CategoriaConteudo]],
        componentes: list[CurricularComponent],
        autor: User,
        qtd_por_canal: int,
    ) -> None:
        """Cria conteúdos variados para cada canal."""
        self.stdout.write(f"📝 Criando {qtd_por_canal} conteúdos por canal...")

        for canal in canais:
            categorias = categorias_por_canal.get(canal.id, [])
            if not categorias:
                self.stdout.write(self.style.WARNING(f"  ⚠ Canal {canal.name} sem categorias, pulando..."))
                continue

            # Filtra tipos permitidos pelo canal (se configurado)
            tipos_permitidos = list(canal.tipos_permitidos.all()) if hasattr(canal, 'tipos_permitidos') else tipos
            if not tipos_permitidos:
                tipos_permitidos = tipos

            for i in range(qtd_por_canal):
                tipo = self.fake.random_element(tipos_permitidos)
                categoria = self.fake.random_element(categorias)
                licenca = self.fake.random_element(licencas) if self.fake.random_int(1, 100) <= 80 else None

                # Gera título único
                titulo_base = self.fake.sentence(nb_words=6).rstrip(".")
                titulo = titulo_base
                contador = 1
                while ConteudoPage.objects.filter(title=titulo).exists():
                    contador += 1
                    titulo = f"{titulo_base} {contador}"

                # Gera slug único
                slug_base = titulo.lower()[:50].replace(" ", "-")
                slug = slug_base
                contador_slug = 1
                while ConteudoPage.objects.filter(slug=slug).exists():
                    contador_slug += 1
                    slug = f"{slug_base}-{contador_slug}"

                # Seleciona 1-3 componentes curriculares
                qtd_componentes = self.fake.random_int(min=1, max=min(3, len(componentes)))
                componentes_selecionados = self.fake.random_elements(componentes, length=qtd_componentes, unique=True)

                conteudo = ConteudoPage(
                    title=titulo,
                    slug=slug,
                    draft_title=titulo,
                    tipo=tipo,
                    category=categoria,
                    license=licenca,
                    canal=canal,
                    autor=autor,
                    search_description=self.fake.sentence(nb_words=20),
                    authors=self.fake.name(),
                    source=self.fake.url() if self.fake.random_int(1, 100) <= 30 else "",
                    is_approved=True,
                    is_featured=self.fake.random_int(1, 100) <= 20,
                    is_site=False,
                    options={
                        "acessibilidade": self.fake.random_element([True, False]),
                        "site_associado": self.fake.url() if self.fake.random_int(1, 100) <= 10 else "",
                    },
                )

                # Adiciona como filho do canal
                canal.add_child(instance=conteudo)

                # Define componentes curriculares (M2M precisa ser feito após save)
                conteudo.save_revision().publish()
                conteudo.componentes_curriculares.set(componentes_selecionados)

                # Adiciona tags
                qtd_tags = self.fake.random_int(min=1, max=5)
                tags = [self.fake.word() for _ in range(qtd_tags)]
                conteudo.tags.add(*tags)

                self.stats["conteudos_criados"] += 1

                if (i + 1) % 10 == 0:
                    self.stdout.write(f"  ✓ {i + 1}/{qtd_por_canal} conteúdos criados para {canal.name}")

            self.stdout.write(f"  ✓ Canal {canal.name}: {qtd_por_canal} conteúdos criados")

    def _imprimir_resumo(self) -> None:
        """Imprime resumo final da execução."""
        self.stdout.write(self.style.SUCCESS("\n" + "=" * 60))
        self.stdout.write(self.style.SUCCESS("📊 RESUMO DA POPULAÇÃO"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(f"  Canais criados:           {self.stats['canais_criados']}")
        self.stdout.write(f"  Conteúdos criados:        {self.stats['conteudos_criados']}")
        self.stdout.write(f"  Tipos criados:            {self.stats['tipos_criados']}")
        self.stdout.write(f"  Licenças criadas:         {self.stats['licencas_criadas']}")
        self.stdout.write(f"  Categorias criadas:       {self.stats['categorias_criadas']}")
        self.stdout.write(f"  Componentes curriculares: {self.stats['componentes_criados']}")
        self.stdout.write(self.style.SUCCESS("=" * 60))

        # Verificação rápida de hierarquia
        homepage = HomePage.objects.filter(depth=2).first()
        if homepage:
            canais_count = CanalPage.objects.live().child_of(homepage).count()
            conteudos_count = ConteudoPage.objects.live().child_of(homepage).count()
            self.stdout.write(f"\n🔍 Verificação de hierarquia:")
            self.stdout.write(f"  HomePage: {homepage.title} (id={homepage.id})")
            self.stdout.write(f"  Canais filhos da Home: {canais_count}")
            self.stdout.write(f"  Conteúdos netos da Home: {conteudos_count}")

    @transaction.atomic
    def handle(self, *args, **options):
        forcereset = options["forcereset"]
        qtd_canais = options["canais"]
        qtd_conteudos = options["conteudos_por_canal"]
        skip_curriculo = options["skip_curriculo"]

        self.stdout.write(self.style.NOTICE("\n🚀 Iniciando população do banco de dados..."))
        self.stdout.write(f"   Canais: {qtd_canais} | Conteúdos por canal: {qtd_conteudos}")

        # 1. Limpeza segura
        self._limpar_dados_teste(forcereset)

        # 2. HomePage
        homepage = self._get_or_create_homepage()

        # 3. Dados de referência (tipos, licenças)
        tipos = self._criar_tipos()
        licencas = self._criar_licencas()

        # 4. Dados curriculares (opcional)
        if not skip_curriculo:
            niveis, categorias_comp, componentes = self._criar_dados_curriculares()
        else:
            self.stdout.write("⏭️  Pulando criação de dados curriculares (--skip-curriculo)")
            # Cria mínimos para FKs obrigatórias
            nivel, _ = NivelEnsino.objects.get_or_create(
                slug="1ano-ef",
                defaults={"name": "1º ano do Ensino Fundamental", "ordem": 1, "is_active": True}
            )
            cat_comp, _ = CurricularComponentCategory.objects.get_or_create(
                slug="linguagens",
                defaults={"name": "Linguagens", "ordem": 1, "is_active": True}
            )
            componentes = [CurricularComponent.objects.get_or_create(
                name="Língua Portuguesa — 1º ano",
                nivel=nivel,
                category=cat_comp,
                defaults={"slug": "lingua-portuguesa-1ano-ef", "ordem": 1, "is_active": True}
            )[0]]

        # 5. Usuário autor
        autor = self._criar_usuario_autor()

        # 6. Canais
        canais = self._criar_canais(homepage, qtd_canais)

        # 7. Categorias por canal
        categorias_por_canal = self._criar_categorias_por_canal(canais)

        # 8. Conteúdos
        self._criar_conteudos(
            canais=canais,
            tipos=tipos,
            licencas=licencas,
            categorias_por_canal=categorias_por_canal,
            componentes=componentes,
            autor=autor,
            qtd_por_canal=qtd_conteudos,
        )

        # 9. Resumo
        self._imprimir_resumo()

        self.stdout.write(self.style.SUCCESS("\n✅ População concluída com sucesso!"))