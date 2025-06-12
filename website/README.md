# Sistema de Irrigação Automático e Inteligente | SIIA | Flask

Este é um projeto de estufa automática (chamado de SIIA), essa parte utiliza o framework Flask para criar uma interface web e integrando inteligência artificial para análise de dados e tomada de decisões.

## Configuração do Ambiente

1. **Instale o Python**: Certifique-se de ter o Python instalado em sua máquina. Você pode baixar e instalar o Python em [python.org](https://www.python.org/).

2. **Instale as Dependências do Projeto**: No terminal, navegue até a pasta do projeto e execute o seguinte comando para instalar as dependências necessárias:

    ```bash
    pip install Flask Flask-SQLAlchemy flask-login psycopg2 scikit-learn matplotlib opencv-python-headless python-dotenv paho-mqtt argon2-cffi firebase-admin
    ```

3. **Configure o Banco de Dados**: Certifique-se de ter o PostgreSQL instalado e configurado em sua máquina. Crie um banco de dados e uma tabela para armazenar os dados da estufa. Aqui está um exemplo de tabela:

    ```sql
    CREATE TABLE dados (
        id SERIAL PRIMARY KEY,
        timestamp TIMESTAMP NOT NULL,
        temperatura FLOAT NOT NULL,       
        umidade FLOAT NOT NULL,
        path_image TEXT
    );
    ```

    Crie um arquivo chamado `.env` na pasta do projeto e adicione as seguintes variáveis de ambiente:

    ```env
    DATABASE_URL=postgresql://username:xxxxxxxx@xxxxxxxxx:5432/dbname
    ```

    Para teste, você pode popular a tabela com alguns dados de exemplo que estão no arquivo `init.sql`.

## Executando o Aplicativo

1. **Executar o Aplicativo**: No terminal, navegue até a pasta do projeto e execute o seguinte comando para iniciar o servidor Flask:

    ```bash
    python app.py
    ```

2. **Acessar o Aplicativo**: Abra um navegador da web e vá para o seguinte endereço:

    ```bash
    http://localhost:5000
    ```

    Você deve ver a interface do aplicativo Flask exibindo os dados da estufa.

## Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir uma issue ou enviar um pull request.

## Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para mais detalhes.
