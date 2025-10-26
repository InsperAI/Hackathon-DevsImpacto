import requests
import json

def testar_api(url):
    """
    Testa uma requisição GET para uma URL de API e exibe a resposta.
    """
    print(f"--- Testando Endpoint: {url} ---")
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        print(f"Sucesso! Código de Status: {response.status_code}")

        try:
            dados_json = response.json()
            print("Resposta JSON (formatada):")
            # Imprime o JSON de forma legível (indentado)
            print(json.dumps(dados_json, indent=2, ensure_ascii=False))
            
        except requests.exceptions.JSONDecodeError:
            # Se a resposta não for JSON (ex: HTML ou texto simples)
            print("Resposta não é JSON. Exibindo os primeiros 500 caracteres do texto:")
            print(response.text[:500] + "...")

    except requests.exceptions.HTTPError as http_err:
        # Captura erros de status HTTP (4xx ou 5xx)
        print(f"Erro HTTP: {http_err}")
    except requests.exceptions.ConnectionError as conn_err:
        # Captura erros de conexão (ex: DNS falhou, servidor recusou)
        print(f"Erro de Conexão: {conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        # Captura erro de timeout (demorou mais que 10s)
        print(f"Erro de Timeout: {timeout_err}")
    except requests.exceptions.RequestException as err:
        # Captura qualquer outro erro da biblioteca requests
        print(f"Erro inesperado: {err}")
    
    print("-" * (len(url) + 24) + "\n")



url_dados_abertos = "https://portaldatransparencia.gov.br/api-de-dados"
testar_api(url_dados_abertos)