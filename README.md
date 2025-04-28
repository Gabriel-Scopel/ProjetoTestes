
# 📚 BookWise

**BookWise** é um sistema de **biblioteca digital** desenvolvido com **Python** e **Streamlit**, que permite:
- Cadastro e autenticação segura de usuários.
- Gerenciamento de livros (cadastrar, buscar, emprestar, devolver e reservar).
- Histórico de empréstimos e devoluções.
- Backup e validação de integridade dos dados.
- Proteção de informações sensíveis via **criptografia** (Fernet).
- Interface web amigável e fácil de usar.

## 🚀 Funcionalidades

- **Login e Cadastro** de usuários (`comum` ou `administrador`).
- **Cadastro de livros** (Título, Autor, ISBN, Categoria).
- **Busca de livros** por título, autor, ISBN ou categoria.
- **Empréstimo e Devolução** de livros com controle de datas.
- **Reservas** de livros quando indisponíveis (com notificação automática).
- **Histórico pessoal** de ações (empréstimos e devoluções).
- **Backup** de dados manual.
- **Criptografia** de todas as informações salvas localmente.
- **Hash seguro** de senhas.

## 🛠️ Tecnologias Utilizadas

- **Python 3.8+**
- **Streamlit** (para a interface web)
- **cryptography (Fernet)** (para criptografia dos dados)
- **hashlib** (para hashing de senhas)
- **JSON** (para persistência de dados)

## 🔒 Segurança
- Todas as informações (usuários, livros, empréstimos e logs) são **criptografadas** antes de serem armazenadas.
- As senhas são **hashadas** utilizando **SHA-256**.
- Arquivos:
  - `bookwise_data.txt` - contém todos os dados criptografados.
  - `bookwise_key.key` - contém a chave de criptografia (não compartilhe!).

## 📦 Como Executar

1. Clone o repositório:

```bash
git clone https://github.com/seu-usuario/bookwise.git
cd bookwise
```

2. Instale as dependências:

```bash
pip install -r streamlit cryptography
```


3. Rode a aplicação:

```bash
streamlit run bookwise_app.py
```

> O sistema criará automaticamente os arquivos `bookwise_data.txt` e `bookwise_key.key` na primeira execução.

## 📝 Estrutura Básica

```plaintext
bookwise/
│
├── bookwise_app.py         # Código principal da aplicação
├── bookwise_data.txt        # Dados criptografados (gerado automaticamente)
├── bookwise_key.key         # Chave de criptografia (gerado automaticamente)
├── README.md
└── requirements.txt
```

