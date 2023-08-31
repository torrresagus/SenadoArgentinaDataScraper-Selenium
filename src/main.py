from urllib.parse import urljoin
from selenium.webdriver.support.ui import Select, WebDriverWait

from apify import Actor
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time
from bs4 import BeautifulSoup
import json


async def main():
    async with Actor:
        # Read the Actor input
        actor_input = await Actor.get_input() or {}
        start_urls = actor_input.get('start_urls', [{'url': 'https://www.senado.gob.ar/parlamentario/parlamentaria/'}])
        max_depth = actor_input.get('max_depth', 1)

        if not start_urls:
            Actor.log.info('No start URLs specified in actor input, exiting...')
            await Actor.exit()

        # Launch a new Selenium Chrome WebDriver
        Actor.log.info('Launching Chrome WebDriver...')
        chrome_options = ChromeOptions()
        if Actor.config.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(options=chrome_options)

        for start_url in start_urls:
            url = start_url.get('url')
            Actor.log.info(f'Scraping {url} ...')

            # Open the URL in the Selenium WebDriver
            driver.get(url)
            
            errors = await validate_form_data_selenium(driver, actor_input)
            if errors:
                Actor.log.info(f'Errores: {errors}')
                await Actor.push_data({
                    "Errores": errors
                })
                driver.quit()
                return

            # Definimos un tiempo máximo de espera (por ejemplo, 10 segundos)
            wait = WebDriverWait(driver, 10)

            # Espera hasta que el elemento esté presente y después haz clic en él
            element_to_click = wait.until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="accordion2"]/div[3]/div[3]/div[1]/a'))
            )
            
            element_to_click.click()
            
            Actor.log.info('Click en el apartado de avanzada ...')
            
            # Fill the form using values from actor_input

            Actor.log.info('Llenado del formulario ...')
            # Autor
            
            desired_value = actor_input['autor']
            driver.execute_script(f'document.querySelector("#busqueda_proyectos_autor").value = "{desired_value}";')
            Actor.log.info('Autor: Listo ...')
            
            time.sleep(0.85)
            
            # Tipo de documento
            if 'tipo_documento' in actor_input:
            # Configurar el campo 'Tipo de Documento'
                Select(driver.find_element(By.XPATH, '//*[@id="busqueda_proyectos_tipoDocumento"]')).select_by_value(actor_input['tipo_documento'].upper())
                Actor.log.info('Tipo Documento: Listo ...')
            # Origen Expediente
            if 'origen_expediente' in actor_input:
                Select(driver.find_element(By.XPATH, '/html/body/div[2]/div[1]/div/div/div[3]/div/div/div/div/div[3]/div[3]/div[3]/div[2]/div/div/form/div[3]/div[1]/select')).select_by_value(actor_input['origen_expediente'].upper()) 
                Actor.log.info('Origen Expediente: Listo ...')
            # Numero / Año
            if 'numero' in actor_input:
                driver.find_element(By.XPATH, '/html/body/div[2]/div[1]/div/div/div[3]/div/div/div/div/div[3]/div[3]/div[3]/div[2]/div/div/form/div[3]/div[2]/input').send_keys(actor_input['numero'])
                Actor.log.info('Numero: Listo ...')
            if 'año' in actor_input:
                Select(driver.find_element(By.XPATH, '/html/body/div[2]/div[1]/div/div/div[3]/div/div/div/div/div[3]/div[3]/div[3]/div[2]/div/div/form/div[3]/div[3]/select')).select_by_value(actor_input['año'])
                Actor.log.info('Año: Listo ...')
            # Palabra Clave 1
            if 'palabra_clave' in actor_input:
                driver.find_element(By.XPATH, '//*[@id="busqueda_proyectos_palabra"]').send_keys(actor_input['palabra_clave'])
                Actor.log.info('Palabra Clave 1: Listo ...')
            #  Opcion Y u O palabras clave
            if 'opcion' in actor_input:
                Select(driver.find_element(By.XPATH, '//*[@id="busqueda_proyectos_opcion"]')).select_by_value(actor_input['opcion'].upper())
                Actor.log.info('Opcion: Listo ...')
            # Palabra Clave 2
            if 'segunda_palabra_clave' in actor_input:
                driver.find_element(By.XPATH, '/html/body/div[2]/div[1]/div/div/div[3]/div/div/div/div/div[3]/div[3]/div[3]/div[2]/div/div/form/div[1]/div[4]/input').send_keys(actor_input['segunda_palabra_clave'])
                Actor.log.info('Palabra Clave 2: Listo ...')
            # Comisiones
            if 'comisiones' in actor_input:
                comisiones = Select(driver.find_element(By.XPATH, '/html/body/div[2]/div[1]/div/div/div[3]/div/div/div/div/div[3]/div[3]/div[3]/div[2]/div/div/form/div[1]/div[5]/select')).select_by_value(actor_input['comisiones'])
                Actor.log.info('Comisiones: Listo ...')
            if 'tipo_expediente' in actor_input:
                Select(driver.find_element(By.XPATH, '/html/body/div[2]/div[1]/div/div/div[3]/div/div/div/div/div[3]/div[3]/div[3]/div[2]/div/div/form/div[3]/div[4]/select')).select_by_value(actor_input['tipo_expediente'].upper())  
                Actor.log.info('Tipo Expediente: Listo ...')
                
            # Click on the search button
            Actor.log.info('Enviando Formulario ...')
            button = driver.find_element(By.XPATH, '/html/body/div[2]/div[1]/div/div/div[3]/div/div/div/div/div[3]/div[3]/div[3]/div[2]/div/div/form/input[1]')
            driver.execute_script("arguments[0].click();", button)

            driver.implicitly_wait(15)  # espera hasta 10 segundos si es necesario
            
            # Verificar si hay un mensaje "Sin Resultados".
            sin_resultados_element = None
            try:
                sin_resultados_element = driver.find_element(By.XPATH, '//div[contains(@class, "alert-info")]/strong[text()=" Sin Resultados"]')
            except:
                pass

            if sin_resultados_element:
                Actor.log.info('No se encontraron resultados para la búsqueda.')
                await Actor.push_data({'result': 'No se encontraron resultados'})
            else:
                # Buscar el elemento y extraer el texto
                try:
                    element_to_extract = driver.find_element(By.XPATH, '/html/body/div[2]/div[1]/div/div/div[2]/div/div/p')
                    texto_extraido = element_to_extract.text
                    texto_limpio = texto_extraido.replace("Cantidad total de registros : ", "")

                    # Agregar el texto extraído como un parámetro a la URL
                    new_url = urljoin(driver.current_url, f'?cantRegistros={texto_limpio}')
                    Actor.log.info(f'Nueva URL: {new_url}')
                    
                    # Abrir la nueva URL con las mismas cookies que la URL anterior
                    driver.get(new_url)
                    
                    # Obtener el HTML de la página
                    page_source = driver.page_source

                    # Parsear el HTML con BeautifulSoup
                    soup = BeautifulSoup(page_source, 'html.parser')

                    # Encontrar la tabla en el HTML
                    table = soup.find("table", {"class": "table table-bordered"})

                    # Inicializar una lista para guardar los datos
                    data = []
                    
                    # Iterar sobre cada fila de la tabla
                    for row in table.find_all('tr')[1:]:  # Saltar el encabezado
                        cells = row.find_all('td')
                        exp = cells[0].text.strip()
                        tipo = cells[1].text.strip()
                        origen = cells[2].text.strip()
                        extracto = cells[3].text.strip()
                        
                        # Añadir un diccionario con los datos de la fila a la lista
                        data.append({
                            'Exp': exp,
                            'Tipo': tipo,
                            'Origen': origen,
                            'Extracto': extracto
                        })
                        
                    json_data = json.dumps(data, indent=4, ensure_ascii=False)

                except Exception as e:
                    Actor.log.info(f'Error al extraer el texto o modificar la URL: {str(e)}')

                data_to_extract = driver.find_element(By.XPATH, '//*[@id="1"]/table/tbody/tr/td[4]').text
                await Actor.push_data(json.loads(json_data))

        driver.quit()
    

async def validate_form_data_selenium(driver, actor_input):
    errors = []

    # Validar el campo 'Autor'
    autor_element = Select(driver.find_element(By.XPATH, '/html/body/div[2]/div[1]/div/div/div[3]/div/div/div/div/div[3]/div[3]/div[3]/div[2]/div/div/form/div[1]/div[1]/select'))
    autor_options = [option.get_attribute('value') for option in autor_element.options]
    if actor_input.get('autor') and actor_input['autor'].upper() not in autor_options:
        errors.append("El valor para 'autor' no es válido")

    # Validar el Campo 'Año'
    año_element = Select(driver.find_element(By.XPATH, '/html/body/div[2]/div[1]/div/div/div[3]/div/div/div/div/div[3]/div[3]/div[3]/div[2]/div/div/form/div[3]/div[3]/select'))
    año_options = [option.get_attribute('value') for option in año_element.options]
    if actor_input.get('año') and actor_input['año'].upper() not in año_options:
        errors.append("El valor para 'año' no es válido")

    # Validar el campo 'Tipo de Documento'
    tipo_documento_element = Select(driver.find_element(By.XPATH, '//*[@id="busqueda_proyectos_tipoDocumento"]'))
    tipo_documento_options = [option.get_attribute('value') for option in tipo_documento_element.options]
    if actor_input.get('tipo_documento') and actor_input['tipo_documento'].upper() not in tipo_documento_options:
        errors.append("El valor para 'tipoDocumento' no es válido")

    # Validar el campo 'Origen del Expediente'
    origen_expediente_element = Select(driver.find_element(By.XPATH, '/html/body/div[2]/div[1]/div/div/div[3]/div/div/div/div/div[3]/div[3]/div[3]/div[2]/div/div/form/div[3]/div[1]/select'))
    origen_expediente_options = [option.get_attribute('value') for option in origen_expediente_element.options]
    if actor_input.get('origen_expediente') and actor_input['origen_expediente'].upper() not in origen_expediente_options:
        errors.append("El valor para 'Origen del Expediente' no es válido")

    # Validar el campo 'Comisiones'
    comisiones_element = Select(driver.find_element(By.XPATH, '/html/body/div[2]/div[1]/div/div/div[3]/div/div/div/div/div[3]/div[3]/div[3]/div[2]/div/div/form/div[1]/div[5]/select'))
    comisiones_options = [option.get_attribute('value') for option in comisiones_element.options]
    if actor_input.get('comisiones') and actor_input['comisiones'].upper() not in comisiones_options:
        errors.append("El valor para 'Comisiones' no es válido")

    # Validar el campo 'Tipo de Expediente'
    tipo_expediente_element = Select(driver.find_element(By.XPATH, '/html/body/div[2]/div[1]/div/div/div[3]/div/div/div/div/div[3]/div[3]/div[3]/div[2]/div/div/form/div[3]/div[4]/select'))
    tipo_expediente_options = [option.get_attribute('value') for option in tipo_expediente_element.options]
    if actor_input.get('tipo_expediente') and actor_input['tipo_expediente'].upper() not in tipo_expediente_options:
        errors.append("El valor para 'Tipo de Expediente' no es válido")

    return errors
