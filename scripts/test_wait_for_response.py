"""
Script de prueba para verificar wait_for_response en Playwright.
"""

import sys
import asyncio
from pathlib import Path

# Agregar el directorio raíz del proyecto al path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from playwright.async_api import async_playwright


async def test_wait_for_response():
    """Prueba si wait_for_response está disponible en el objeto page."""
    print("Iniciando prueba de wait_for_response...")
    
    playwright = await async_playwright().start()
    
    try:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        print(f"Tipo de page: {type(page)}")
        print(f"¿Tiene wait_for_response?: {hasattr(page, 'wait_for_response')}")
        print(f"¿Está en dir?: {'wait_for_response' in dir(page)}")
        
        # Intentar acceder al método directamente
        try:
            method = getattr(page, 'wait_for_response', None)
            print(f"Método obtenido: {method}")
            print(f"Tipo del método: {type(method)}")
            if method:
                print("✓ wait_for_response está disponible")
            else:
                print("✗ wait_for_response NO está disponible")
        except Exception as e:
            print(f"Error al obtener método: {e}")
        
        # Verificar métodos disponibles relacionados con response
        response_methods = [m for m in dir(page) if 'response' in m.lower()]
        print(f"Métodos relacionados con 'response': {response_methods}")
        
        await browser.close()
        
    finally:
        await playwright.stop()


if __name__ == "__main__":
    asyncio.run(test_wait_for_response())
