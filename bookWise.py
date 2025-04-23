from datetime import datetime, timedelta
import streamlit as st
import json
import os
import hashlib
import base64
from cryptography.fernet import Fernet

class Usuario:
    def __init__(self, nome, email, senha, tipo="comum"):
        self.nome = nome
        self.email = email
        self.senha = senha  # Senha já será armazenada em forma de hash
        self.tipo = tipo
        self.historico = []
    
    def to_dict(self):
        return {
            "nome": self.nome,
            "email": self.email,
            "senha": self.senha,
            "tipo": self.tipo,
            "historico": [(titulo, status, data.isoformat()) for titulo, status, data in self.historico]
        }
    
    @classmethod
    def from_dict(cls, data):
        usuario = cls(data["nome"], data["email"], data["senha"], data["tipo"])
        usuario.historico = [(titulo, status, datetime.fromisoformat(data)) 
                             for titulo, status, data in data.get("historico", [])]
        return usuario

class Livro:
    def __init__(self, titulo, autor, isbn, categoria):
        self.titulo = titulo
        self.autor = autor
        self.isbn = isbn
        self.categoria = categoria
        self.disponivel = True
        self.reservas = []
        self.data_devolucao = None
    
    def to_dict(self):
        return {
            "titulo": self.titulo,
            "autor": self.autor,
            "isbn": self.isbn,
            "categoria": self.categoria,
            "disponivel": self.disponivel,
            "reservas": self.reservas,
            "data_devolucao": self.data_devolucao.isoformat() if self.data_devolucao else None
        }
    
    @classmethod
    def from_dict(cls, data):
        livro = cls(data["titulo"], data["autor"], data["isbn"], data["categoria"])
        livro.disponivel = data["disponivel"]
        livro.reservas = data["reservas"]
        livro.data_devolucao = datetime.fromisoformat(data["data_devolucao"]) if data["data_devolucao"] else None
        return livro

class Biblioteca:
    def __init__(self):
        self.usuarios = {}
        self.livros = {}
        self.emprestimos = {}
        self.logs = []
        self.backups = []
        self.chave_cripto = self._gerar_ou_carregar_chave()
        self.carregar_dados()

    def _gerar_ou_carregar_chave(self):
        """Gera ou carrega uma chave criptográfica"""
        chave_arquivo = "bookwise_key.key"
        if os.path.exists(chave_arquivo):
            with open(chave_arquivo, "rb") as arquivo_chave:
                return arquivo_chave.read()
        else:
            chave = Fernet.generate_key()
            with open(chave_arquivo, "wb") as arquivo_chave:
                arquivo_chave.write(chave)
            return chave
    
    def _criptografar(self, texto):
        """Criptografa um texto"""
        f = Fernet(self.chave_cripto)
        return f.encrypt(texto.encode()).decode()
    
    def _descriptografar(self, texto_cifrado):
        """Descriptografa um texto"""
        f = Fernet(self.chave_cripto)
        return f.decrypt(texto_cifrado.encode()).decode()
    
    def _hash_senha(self, senha):
        """Cria um hash seguro da senha"""
        return hashlib.sha256(senha.encode()).hexdigest()

    def log(self, acao):
        self.logs.append((datetime.now(), acao))

    def salvar_dados(self):
        """Salva todos os dados da biblioteca em arquivos."""
        # Preparar dados para salvar
        dados = {
            "usuarios": {email: usuario.to_dict() for email, usuario in self.usuarios.items()},
            "livros": {isbn: livro.to_dict() for isbn, livro in self.livros.items()},
            "emprestimos": {
                isbn: [email, data_devolucao.isoformat()] 
                for isbn, (email, data_devolucao) in self.emprestimos.items()
            },
            "logs": [(data.isoformat(), acao) for data, acao in self.logs]
        }
        
        # Converter para JSON e criptografar
        json_dados = json.dumps(dados)
        dados_criptografados = self._criptografar(json_dados)
        
        # Salvar em arquivo
        with open("bookwise_data.txt", "w") as arquivo:
            arquivo.write(dados_criptografados)
            
        return True

    def carregar_dados(self):
        """Carrega todos os dados da biblioteca de arquivos."""
        try:
            if os.path.exists("bookwise_data.txt"):
                with open("bookwise_data.txt", "r") as arquivo:
                    dados_criptografados = arquivo.read()
                
                # Descriptografar e carregar dados
                json_dados = self._descriptografar(dados_criptografados)
                dados = json.loads(json_dados)
                
                # Reconstruir objetos
                self.usuarios = {email: Usuario.from_dict(usuario_data) 
                                for email, usuario_data in dados["usuarios"].items()}
                
                self.livros = {isbn: Livro.from_dict(livro_data) 
                              for isbn, livro_data in dados["livros"].items()}
                
                self.emprestimos = {
                    isbn: (email, datetime.fromisoformat(data))
                    for isbn, [email, data] in dados["emprestimos"].items()
                }
                
                self.logs = [(datetime.fromisoformat(data), acao) 
                           for data, acao in dados["logs"]]
                
                return True
        except Exception as e:
            st.error(f"Erro ao carregar dados: {str(e)}")
            return False

    def cadastrar_usuario(self, nome, email, senha, tipo="comum"):
        if email in self.usuarios:
            raise ValueError("Usuário já cadastrado.")
        if not nome or not email or not senha or tipo not in ["comum", "administrador"]:
            raise ValueError("Dados inválidos para cadastro de usuário.")
        
        # Hash da senha antes de armazenar
        senha_hash = self._hash_senha(senha)
        self.usuarios[email] = Usuario(nome, email, senha_hash, tipo)
        self.log(f"Usuário cadastrado: {email} ({tipo})")
        self.salvar_dados()  # Salvar após cadastro

    def autenticar_usuario(self, email, senha):
        usuario = self.usuarios.get(email)
        senha_hash = self._hash_senha(senha)
        if usuario and usuario.senha == senha_hash:
            self.log(f"Login bem-sucedido: {email}")
            return usuario
        self.log(f"Tentativa de login falhou: {email}")
        raise ValueError("Credenciais inválidas.")

    def cadastrar_livro(self, titulo, autor, isbn, categoria):
        if isbn in self.livros:
            raise ValueError("Livro já cadastrado.")
        self.livros[isbn] = Livro(titulo, autor, isbn, categoria)
        self.log(f"Livro cadastrado: {isbn} - {titulo}")
        self.salvar_dados()  # Salvar após cadastro

    def buscar_livros(self, termo):
        return [livro for livro in self.livros.values()
                if termo.lower() in livro.titulo.lower()
                or termo.lower() in livro.autor.lower()
                or termo.lower() in livro.categoria.lower()
                or termo.lower() in livro.isbn.lower()]

    def emprestar_livro(self, email, isbn):
        usuario = self.usuarios[email]
        livro = self.livros[isbn]
        if not livro.disponivel:
            raise ValueError("Livro indisponível para empréstimo.")
        livro.disponivel = False
        livro.data_devolucao = datetime.now() + timedelta(days=7)
        self.emprestimos[isbn] = (email, livro.data_devolucao)
        usuario.historico.append((livro.titulo, "emprestado", datetime.now()))
        self.log(f"Livro emprestado: {isbn} para {email}")
        self.salvar_dados()  # Salvar após empréstimo

    def devolver_livro(self, isbn):
        if isbn not in self.emprestimos:
            raise ValueError("Livro não está emprestado.")
        email, _ = self.emprestimos.pop(isbn)
        livro = self.livros[isbn]
        livro.disponivel = True
        livro.data_devolucao = None
        usuario = self.usuarios[email]
        usuario.historico.append((livro.titulo, "devolvido", datetime.now()))
        self.log(f"Livro devolvido: {isbn} por {email}")
        self.salvar_dados()  # Salvar após devolução
        
        st.success(f"Livro '{livro.titulo}' devolvido com sucesso por {usuario.nome}!")
        if livro.reservas:
            proximo_usuario_email = livro.reservas.pop(0)
            st.info(f"Livro '{livro.titulo}' agora está disponível para {proximo_usuario_email}.")
            self.log(f"Notificação enviada para reserva de {proximo_usuario_email} - {isbn}")

    def reservar_livro(self, email, isbn):
        livro = self.livros[isbn]
        if livro.disponivel:
            raise ValueError("Livro disponível para empréstimo. Não é necessário reservar.")
        if email in livro.reservas:
            raise ValueError("Usuário já está na fila de reserva.")
        livro.reservas.append(email)
        self.log(f"Reserva registrada: {isbn} por {email}")
        self.salvar_dados()  # Salvar após reserva

    def historico_usuario(self, email):
        return self.usuarios[email].historico

    def livros_emprestados_ao_usuario(self, email):
        livros_emprestados = []
        for isbn, (usuario_email, data_devolucao) in self.emprestimos.items():
            if usuario_email == email:
                livro = self.livros[isbn]
                livros_emprestados.append({
                    'livro': livro,
                    'isbn': isbn,
                    'data_devolucao': data_devolucao
                })
        return livros_emprestados

    def backup(self):
        backup_data = {
            "usuarios": list(self.usuarios.keys()),
            "livros": list(self.livros.keys()),
            "emprestimos": list(self.emprestimos.keys()),
            "data": datetime.now().isoformat()
        }
        self.backups.append(backup_data)
        self.log("Backup executado")
        self.salvar_dados()  # Salvar após backup
        return True

    def validar_integridade(self):
        # Simula verificação da integridade dos dados
        for email, usuario in self.usuarios.items():
            if not usuario.nome or not usuario.email:
                return False
        for isbn, livro in self.livros.items():
            if not livro.titulo or not livro.autor:
                return False
        return True

# Interface Streamlit
st.set_page_config(page_title="BookWise", layout="centered")

if 'biblio' not in st.session_state:
    st.session_state.biblio = Biblioteca()

if 'usuario_logado' not in st.session_state:
    st.session_state.usuario_logado = None

biblio = st.session_state.biblio
usuario_logado = st.session_state.usuario_logado

st.title("📚 BookWise - Biblioteca Digital")

if not usuario_logado:
    tab_login, tab_cadastro = st.tabs(["Login", "Cadastro"])

    with tab_login:
        email = st.text_input("Email", key="login_email")
        senha = st.text_input("Senha", type="password", key="login_senha")
        if st.button("Entrar"):
            try:
                usuario = biblio.autenticar_usuario(email, senha)
                st.session_state.usuario_logado = usuario
                st.success(f"Bem-vindo, {usuario.nome}!")
                st.rerun()
            except ValueError as e:
                st.error(str(e))

    with tab_cadastro:
        nome_cad = st.text_input("Nome", key="cad_nome")
        email_cad = st.text_input("Email de Cadastro", key="cad_email")
        senha_cad = st.text_input("Senha", type="password", key="cad_senha")
        tipo_cad = st.selectbox("Tipo de Usuário", ["comum", "administrador"], key="cad_tipo")
        if st.button("Cadastrar", key="btn_cadastrar"):
            try:
                biblio.cadastrar_usuario(nome_cad, email_cad, senha_cad, tipo_cad)
                st.success("Usuário cadastrado com sucesso!")
            except ValueError as e:
                st.error(str(e))
else:
    st.success(f"Logado como: {usuario_logado.nome} ({usuario_logado.tipo})")
    opcao = st.sidebar.selectbox("Menu", ["Cadastrar Livro", "Buscar Livro", "Meus Livros", "Histórico", "Backup", "Sair"])

    if opcao == "Cadastrar Livro":
        with st.form("form_livro"):
            titulo = st.text_input("Título", key="livro_titulo")
            autor = st.text_input("Autor", key="livro_autor")
            isbn = st.text_input("ISBN", key="livro_isbn")
            categoria = st.text_input("Categoria", key="livro_categoria")
            submitted = st.form_submit_button("Cadastrar")
            if submitted:
                try:
                    biblio.cadastrar_livro(titulo, autor, isbn, categoria)
                    st.success("Livro cadastrado com sucesso.")
                except ValueError as e:
                    st.error(str(e))

    elif opcao == "Buscar Livro":
        termo = st.text_input("Buscar por título, autor, categoria ou ISBN", key="busca_termo")
        if termo:
            resultados = biblio.buscar_livros(termo)
            if not resultados:
                st.info("Nenhum livro encontrado.")
            for livro in resultados:
                st.markdown(f"**{livro.titulo}** — {livro.autor}")
                st.markdown(f"📚 Categoria: {livro.categoria} | Disponível: {livro.disponivel}")
                if livro.disponivel:
                    if st.button(f"Emprestar {livro.isbn}", key=f"emprestar_{livro.isbn}"):
                        try:
                            biblio.emprestar_livro(usuario_logado.email, livro.isbn)
                            st.success("Livro emprestado.")
                            st.rerun()
                        except ValueError as e:
                            st.error(str(e))
                else:
                    if st.button(f"Reservar {livro.isbn}", key=f"reservar_{livro.isbn}"):
                        try:
                            biblio.reservar_livro(usuario_logado.email, livro.isbn)
                            st.success("Livro reservado.")
                        except ValueError as e:
                            st.error(str(e))

    elif opcao == "Meus Livros":
        st.header("Meus Livros Emprestados")
        
        livros_emprestados = biblio.livros_emprestados_ao_usuario(usuario_logado.email)
        
        if not livros_emprestados:
            st.info("Você não possui nenhum livro.")
        else:
            for item in livros_emprestados:
                livro = item['livro']
                isbn = item['isbn']
                data_devolucao = item['data_devolucao']
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**{livro.titulo}** — {livro.autor}")
                    st.markdown(f"📚 Categoria: {livro.categoria}")
                    st.markdown(f"📅 Data de devolução: {data_devolucao.strftime('%d/%m/%Y')}")
                    
                    # Verificar se o livro está atrasado
                    if data_devolucao < datetime.now():
                        st.markdown("⚠️ **ATRASADO**", unsafe_allow_html=True)
                    else:
                        dias_restantes = (data_devolucao - datetime.now()).days
                        st.markdown(f"⏱️ {dias_restantes} dias restantes para devolução")
                
                with col2:
                    if st.button(f"Devolver", key=f"devolver_{isbn}"):
                        try:
                            biblio.devolver_livro(isbn)
                            st.rerun()
                        except ValueError as e:
                            st.error(str(e))
                
                st.markdown("---")

    elif opcao == "Histórico":
        historico = biblio.historico_usuario(usuario_logado.email)
        if not historico:
            st.info("Nenhum histórico encontrado.")
        for item in historico:
            st.write(f"{item[0]} — {item[1]} em {item[2].strftime('%d/%m/%Y %H:%M')}")

    elif opcao == "Backup":
        if biblio.backup():
            st.success("Backup executado com sucesso.")
            st.info("Todos os dados foram salvos com segurança.")

    elif opcao == "Sair":
        st.session_state.usuario_logado = None
        biblio.salvar_dados()  # Salvar dados ao sair
        st.rerun()