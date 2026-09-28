import asyncio
from playwright.async_api import async_playwright

async def test_gestao_conteudos_menu():
    async with async_playwright() as p:
        # Launch browser directly (not via MCP)
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Add console logging
        page.on("console", lambda msg: print(f"CONSOLE: {msg.text}"))
        page.on("pageerror", lambda err: print(f"PAGE ERROR: {err}"))
        page.on("close", lambda: print("PAGE CLOSED"))
        context.on("close", lambda: print("CONTEXT CLOSED"))
        
        # Navigate to admin login (using web service name)
        print("Navigating to login page...")
        await page.goto("http://web:8000/admin/login/?next=/admin/")
        print(f"After goto: {page.url}")
        
        # Login (assuming default superuser credentials or create one)
        print("Filling login form...")
        await page.fill('input[name="username"]', 'admin')
        await page.fill('input[name="password"]', 'admin123')
        await page.click('button[type="submit"]')
        
        # Wait for admin dashboard to load - wait for a specific element instead of networkidle
        print("Waiting for navigation after login...")
        await page.wait_for_load_state("domcontentloaded")
        
        # Wait for the admin dashboard to be visible - try multiple selectors
        print("Waiting for admin dashboard...")
        try:
            await page.wait_for_selector('#header', timeout=5000)
        except:
            try:
                await page.wait_for_selector('.w-header', timeout=5000)
            except:
                await page.wait_for_selector('nav', timeout=5000)
        
        print(f"Current URL after login: {page.url}")
        
        # Check if "Gestão de Conteúdos" menu item exists
        print("Looking for 'Gestão de Conteúdos' menu...")
        menu_item = page.locator('a:has-text("Gestão de Conteúdos")')
        await menu_item.wait_for(state="visible", timeout=10000)
        
        print("✅ Menu 'Gestão de Conteúdos' encontrado e visível!")
        
        # Verify the URL is correct - try multiple ways to get the URL
        href = await menu_item.get_attribute("href")
        print(f"URL do menu (href): {href}")
        
        # Also check the parent element or data attributes
        parent = menu_item.locator('..')
        parent_html = await parent.inner_html()
        print(f"Parent HTML: {parent_html[:500]}")
        
        # Click the menu to verify it navigates correctly
        print("Clicking menu...")
        await menu_item.click()
        await page.wait_for_load_state("domcontentloaded")
        
        print(f"URL after click: {page.url}")
        
        # Check if we're on the create page (should contain /add/ in URL)
        if "/add/" in page.url:
            print("✅ Navegação para criação de ConteudoPage funcionando!")
        else:
            print(f"❌ Navegação FALHOU - ainda na URL: {page.url}")
            # Try to find the create page content
            page_content = await page.content()
            if "Adicionar" in page_content or "Add" in page_content:
                print("⚠️  Conteúdo de criação encontrado mas URL não mudou")
            else:
                print("❌ Página de criação NÃO carregou")
                # Check for permission error or other messages
                if "Permissão" in page_content or "permission" in page_content.lower():
                    print("⚠️  Possível erro de permissão detectado")
                if "não tem permissão" in page_content or "don't have permission" in page_content.lower():
                    print("⚠️  Usuário não tem permissão para criar página")
        
        # Also try navigating directly to the URL to verify it works
        print("\n--- Testando navegação direta para a URL do menu ---")
        full_url = f"http://web:8000{href}"
        print(f"Navegando para: {full_url}")
        await page.goto(full_url)
        await page.wait_for_load_state("domcontentloaded")
        print(f"URL after direct navigation: {page.url}")
        
        page_content = await page.content()
        if "Adicionar" in page_content or "Add" in page_content or "Conteúdo" in page_content:
            print("✅ Página de criação carregou corretamente via navegação direta!")
        else:
            print("❌ Página de criação NÃO carregou via navegação direta")
            if "Permissão" in page_content or "permission" in page_content.lower():
                print("⚠️  Erro de permissão detectado")
            # Print first 2000 chars of page content for debugging
            print(f"Page content preview: {page_content[:2000]}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_gestao_conteudos_menu())