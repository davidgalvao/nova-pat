# interacoes/ — CLAUDE.md

## Papel deste app
`interacoes` reúne toda a interação de usuário com recurso educacional: comentário, like, favorito e avaliação. Depende de `conteudos` (e, para comentário/like, também de `aplicativos`) — nunca o contrário. `conteudos`/`aplicativos` não devem importar nada daqui.

Fonte da verdade: `docs/schema-legado.md`, `docs/requisitos-vs-legado.md`.

## Fase atual: mista
`Comentario` e `Like` são transposição fiel do legado. `FavoritoConteudo` e `AvaliacaoConteudo` são construção nova (RF010/RF011), sem equivalente legado — não presumir regra de negócio "escondida" pra essas duas, elas nasceram desta conversa.

## Models — transposição (Comentario, Like)

### `Comentario`
**Achado importante, corrige suposição anterior**: no legado, comentário **não é exclusivo de conteúdo** — é polimórfico entre `ConteudoPage` e `AplicativoEducacionalPage` (campo `tipo` no legado, com valores literais `'conteudo'`/`'aplicativo'`, mais duas FKs nullable, uma pra cada). Replicar essa fidelidade.

**Resolvido — login e moderação**: comentar exige usuário autenticado (nunca anônimo). Comentário também passa por aprovação antes de publicar — **esta regra não existe no legado** (a tabela `comentarios` original não tem campo de aprovação), é decisão nova da NOVA PAT. Por consistência com o padrão já estabelecido em `conteudos` (RN-L1), replica-se o mesmo critério de papel: comentário de `super-admin`, `admin` ou `coordenador` é publicado direto (`is_approved=True` na criação); qualquer outro usuário entra sempre como `is_approved=False`, pendente de moderação — decidido no servidor, nunca confiado ao front.

```python
class Comentario(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    conteudo = models.ForeignKey('conteudos.ConteudoPage', null=True, blank=True, on_delete=models.CASCADE)
    aplicativo = models.ForeignKey('aplicativos.AplicativoEducacionalPage', null=True, blank=True, on_delete=models.CASCADE)
    body = models.TextField()
    is_approved = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)
    # soft delete — legado usa SoftDeletes, avaliar se replica via campo `deletado_em` ou lib de soft delete do Django
```

Manter a abordagem de duas FKs nullable (fiel ao legado) em vez de introduzir `GenericForeignKey` do Django — para só dois alvos possíveis, a complexidade extra de `ContentType` não se paga. Se um terceiro tipo de alvo aparecer no futuro, reavaliar.

### `Like`
Mesma estrutura polimórfica de `Comentario` (FKs nullable pra `ConteudoPage` e `AplicativoEducacionalPage`). **Resolvido**: é like simples, não like/dislike. Modelo simplificado em relação ao legado — não precisa do campo `like` (boolean nullable) ambíguo: a **existência do registro** já significa "curtiu". Descurtir é **deletar a linha**, não marcar `false`.

```python
class Like(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    conteudo = models.ForeignKey('conteudos.ConteudoPage', null=True, blank=True, on_delete=models.CASCADE)
    aplicativo = models.ForeignKey('aplicativos.AplicativoEducacionalPage', null=True, blank=True, on_delete=models.CASCADE)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('user', 'conteudo'), ('user', 'aplicativo')]
```

## Models — construção nova (Favorito, Avaliação)

### `FavoritoConteudo`
Requer usuário logado — dado pessoal, não engajamento público. Diferente de `Like`: favoritar é uma lista privada do usuário, curtir é sinal público de engajamento.

```python
class FavoritoConteudo(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    conteudo = models.ForeignKey('conteudos.ConteudoPage', on_delete=models.CASCADE)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'conteudo')
```

Escopo atual: só `ConteudoPage`, por decisão explícita. Se favoritar `AplicativoEducacionalPage` também fizer sentido de produto no futuro, é decisão nova a ser tomada — não implementar por analogia sem confirmar.

### `AvaliacaoConteudo`
Nota 1 a 5, pensada para uso futuro em curadoria/ranking — **decisão fechada: não é critério de busca/filtro/ordenação**, só exibição.

```python
class AvaliacaoConteudo(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    conteudo = models.ForeignKey('conteudos.ConteudoPage', on_delete=models.CASCADE)
    nota = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'conteudo')  # permite reeditar, 1 avaliação por par
```

Ao salvar/apagar uma `AvaliacaoConteudo`, um **signal definido neste app** atualiza os campos desnormalizados `media_avaliacao`/`total_avaliacoes` em `ConteudoPage` (campos vivem em `conteudos`, mas a lógica de atualização vive aqui — `conteudos` não deve saber que `interacoes` existe):

```python
@receiver([post_save, post_delete], sender=AvaliacaoConteudo)
def atualizar_media_avaliacao(sender, instance, **kwargs):
    conteudo = instance.conteudo
    agregados = conteudo.avaliacaoconteudo_set.aggregate(media=Avg('nota'), total=Count('id'))
    conteudo.media_avaliacao = agregados['media'] or 0
    conteudo.total_avaliacoes = agregados['total']
    conteudo.save(update_fields=['media_avaliacao', 'total_avaliacoes'])
```

**Nunca usar `media_avaliacao`/`total_avaliacoes` em `WHERE`/`ORDER BY` de busca** — decisão de produto fechada (ver `docs/requisitos-vs-legado.md`, RF011): poucas notas baixas não devem esconder conteúdo bom que só tem pouco engajamento.

## O que NÃO fazer neste app
- Não restringir `Comentario`/`Like` só a `ConteudoPage` — o legado já suporta os dois (conteúdo e aplicativo), tirar isso seria regressão, não simplificação.
- Não permitir comentário de usuário não autenticado.
- Não publicar comentário de usuário comum sem passar por aprovação (`is_approved=False` por padrão, só papéis privilegiados publicam direto).
- Não estender `FavoritoConteudo`/`AvaliacaoConteudo` para `AplicativoEducacionalPage` por conta própria — não foi pedido, é decisão de produto em aberto.
- Não usar `GenericForeignKey` só porque "parece mais elegante" — duas FKs nullable é fiel ao legado e suficiente para dois alvos.
- Não deixar `conteudos` importar nada deste app — a dependência é de mão única.