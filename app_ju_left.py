from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


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


driver = webdriver.Firefox()
wait = WebDriverWait(driver, 15)

driver.get("https://www.princesapop.com")

email = wait.until(EC.presence_of_element_located((By.ID, "email_connexion_mabimbo")))

email.send_keys("juditerm123@gmail.com")

senha = driver.find_element(By.ID, "password_connexion_mabimbo")
senha.send_keys("rangel")

senha.submit()

fechar_cookies(driver)

wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".left img")))

driver.find_element(By.CSS_SELECTOR, ".left img").click()

i = 0
while i < 100:
    stats = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".stats"))).text
    span = wait.until(EC.presence_of_element_located((By.XPATH, "//span[@name='ba']"))).text

    linhas = stats.split("\n")
    valor_stats = pegar_ap(stats)
    valor_span = extrair_numero(span)

    print(valor_stats, valor_span)

    if valor_span > valor_stats:
        i += 1
        wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Enviar um desafio"))).click()
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#btn-challenge-without-stake > .btn"))).click()
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".left img"))).click()
    else:
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".left img"))).click()

driver.quit()