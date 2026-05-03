from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
from dotenv import load_dotenv
import os

load_dotenv()

email_env = os.getenv("EMAIL")
senha_env = os.getenv("SENHA")


def extrair_numero(texto):
    return int(texto.replace("AP", "").replace(" ", "").strip())

def pegar_ap(texto):
    for linha in texto.split("\n"):
        if "AP" in linha:
            return int(linha.replace("AP", "").replace(" ", ""))
    return None

def fechar_cookies(driver):
    wait = WebDriverWait(driver, 10)

    try:
        botao = wait.until(
            EC.element_to_be_clickable((By.ID, "cookiescript_accept"))
        )

        driver.execute_script("arguments[0].click();", botao)

        wait.until(
            EC.invisibility_of_element_located((By.ID, "cookiescript_buttons"))
        )

    except:
        print("Banner de cookies não apareceu ou já foi fechado.")
        
def verificar_popup(driver):
    try:
        popup = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#notification-center p"))
        )

        texto = popup.text.lower()

        if "já enviou um desafio" in texto:
            return "erro"

        elif "lançou um desafio" in texto:
            return "sucesso"

        return "outro"

    except:
        return None


driver = webdriver.Firefox()
wait = WebDriverWait(driver, 7)

driver.get("https://www.princesapop.com")

email = wait.until(EC.presence_of_element_located((By.ID, "email_connexion_mabimbo")))
email.send_keys(email_env)

senha = driver.find_element(By.ID, "password_connexion_mabimbo")
senha.send_keys(senha_env)

senha.submit()

fechar_cookies(driver)

wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".left img")))

driver.find_element(By.CSS_SELECTOR, ".left img").click()

i = 0
while i < 100:
    stats = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".stats"))).text
    span = wait.until(EC.presence_of_element_located((By.XPATH, "//span[@name='ba']"))).text

    valor_stats = pegar_ap(stats)
    valor_span = extrair_numero(span)
    
    if valor_stats is None:
        print("Erro ao pegar AP, pulando...")
        time.sleep(2)
        continue
    

    if valor_span > valor_stats:
        print("princesa elegível a desafio, você ganharia.")
        try:
            wait.until(EC.invisibility_of_element_located((By.ID, "notification-center")))
        except:
            pass
        
        wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Enviar um desafio"))).click()
        time.sleep(random.uniform(1, 2))
        
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#btn-challenge-without-stake > .btn"))).click()
        time.sleep(random.uniform(1, 2))
        
        
        try:
            wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#notification-center p")))
        
        resultado_popup = verificar_popup(driver)

        if resultado_popup == "erro":
            print("Já desafiou anteriormente, pulando princesa...")
        elif resultado_popup == "sucesso":
            print("Desafio enviado com sucesso, avançando princesa...")
            i += 1
        else:
            print("Popup inesperado")
            
        wait.until(EC.invisibility_of_element_located((By.ID, "notification-center")))
        
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".left img"))).click()
        
    else:
        print("Princesa não elegível a desafio, você perderia.")
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".left img"))).click()
        
    time.sleep(random.uniform(2, 5))
    
    if i % 10 == 0 and i != 0:
        time.sleep(random.uniform(10, 20))

driver.quit()