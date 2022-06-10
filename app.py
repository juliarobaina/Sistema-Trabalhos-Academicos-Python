from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import bcrypt #poderia ter usado o Flask-Bcrypt

#criando uma instância do Flask, __name__ pega o nome do arquivo ou pacote para que o flask saiba o local dos arquivos, valor padrão de __name__ é main
app = Flask(__name__)

#configuraão do BD
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'sistemaprogweb'

#abrir conexão
mysql = MySQL(app)

def usuariosComMesmoEmail(dados, email, idUsuario = False):
    '''Não pode existir usuários diferentes com o mesmo endereço de e-mail.
       Parâmetro idUsuario é opcional, pois se a chamada foi feita da função 
       cadastrarUsuario, esse usuário por ainda não existir no banco não possuirá id'''
    
    for k in range(len(dados)):     
        if email in dados[k]:
            if idUsuario != dados[k][0]:
                #email já cadastrado ou usuários diferentes querendo ter o mesmo e-mail
                return True
            else:
                return False
    return False

def removerMuitosEspacosEntrePalavras(nome):
    '''Exemplo: Manga     mamão   maçã; vai ficar -> Manga mamão maçã
        1º separar as strings
        2º adicionar somente 1 espaço entre elas
    '''
    nomeSplit = nome.split()
    nomeCerto = ''
    for i in range(len(nomeSplit)):
        if(i + 1 != len(nomeSplit)):
            nomeCerto = nomeCerto + nomeSplit[i] + ' '
        else:
            nomeCerto = nomeCerto + nomeSplit[i]
    return nomeCerto

#hash para senha
def gerarSenha(senha):
    '''Cria um hash da senha com o Bcrypt, adicionando caracteres aleatórios pelo método gensalt, para a senha ser inserida no banco'''
    
    #para que a senha esteja em bytes, por causa do método hashpw
    senha = senha.encode('utf-8')
    #obtendo o hash da senha. bcrypt.gensalt tem um custo padrão de 10. Quanto maior o valor, maior será o custo e o tempo para gerar o hash
    hashed = bcrypt.hashpw(senha, bcrypt.gensalt())
    return hashed

#encriptando a comunicação das sessions entre o cliente e o servidor
app.secret_key = gerarSenha("teste")

#Index
@app.route("/")
def index():
    return render_template("index.html")

#Página de cadastrar usuário
@app.route("/cadastrar")
def cadastrar():
    return render_template("cadastrar.html")

#Inserir um novo usuário
@app.route("/cadastrarUsuario", methods = ["POST"])
def cadastrarUsuario():
    if request.method == 'POST':
        nome = request.form["nome"].strip()
        email = request.form["email"].replace(' ', '')
        senha = request.form["senha"]

        nome = removerMuitosEspacosEntrePalavras(nome)     

        if nome and email and senha:
            db = mysql.connection.cursor()

            db.execute("SELECT * FROM usuarios")

            dados = db.fetchall()
                    
            #Não pode ter mais de um usuario com o mesmo email
            if(usuariosComMesmoEmail(dados, email)):
                return redirect(url_for('cadastrar'))

            #hash para senha
            senha = gerarSenha(senha)   

            db.execute('INSERT INTO usuarios (nome, email, senha) VALUES (%s,%s,%s)', (nome, email, senha))

            mysql.connection.commit()

            db.close()

            return redirect(url_for('cadastrar'))
        else:
            
           return redirect(url_for('cadastrar'))

#Página de alterar usuário
@app.route("/alterar")
def alterar():
    return render_template("alterar.html")

#Atualizar um usuário
@app.route("/alterarUsuario", methods = ["POST"])
def alterarUsuario():

    if request.method == 'POST':
       # idUsuario = request.form["idUsuario"]
        nome = request.form["nome"].strip() #strip, remove os espaços em branco do início e fim da string
        email = request.form["email"].replace(' ', '')
        idUsuario = 24

        #Criar um alterar senha separado

        nome = removerMuitosEspacosEntrePalavras(nome)

        if nome and email:
            db = mysql.connection.cursor()

            db.execute("SELECT * FROM usuarios")

            dados = db.fetchall()

            #não pode usuários com o mesmo e-mail
            if(usuariosComMesmoEmail(dados, email, idUsuario)):
                return redirect(url_for('alterar'))

            #tupla com os valores do usuário
            val = (nome, email, idUsuario)
            db.execute("UPDATE usuarios SET nome = %s, email = %s WHERE id = %s", val)

            mysql.connection.commit()

            db.close()

            return redirect(url_for('alterar'))
        else:
            
           return redirect(url_for('alterar'))

#Página login usuário
@app.route("/login")
def login():
    
    return render_template("login.html")


#Logar o usuário
@app.route("/loginUsuario", methods = ["POST"])
def loginUsuario():

    if request.method == "POST":
        email = request.form["email"].replace(' ','')
        senha = request.form["senha"]

        #para ficar em bytes
        novaSenha = senha.encode("utf-8")

        db = mysql.connection.cursor()

        db.execute("SELECT * FROM usuarios")
        
        dados = db.fetchall()
        
        for i in range(len(dados)):
            if email in dados[i]:
                #para ficar em bytes. str -> bytes
                senhaEncode = dados[i][3].encode("utf-8")
                if bcrypt.checkpw(novaSenha,senhaEncode):#as senhas correspondem. Acesso permitido
                    session["nome"] = dados[i][1] #criando e inicializando a session nome
                    return redirect(url_for('meuPainel'))

#Página inicial do perfil de cada usuário
@app.route('/meupainel')
def meuPainel():
    
    usuario = None
  
    if "nome" in session: #verifica se existe a session nome
        return render_template("meupainel.html", usuario = session["nome"]) #retorna o valor da session para a página login.html através do parâmetro usuario
    #lembrete: fazer session id

#Sair da conta do usuário
@app.route('/logout')
def logout():
    
    session.pop('nome', None)
    '''
        session.pop('nome', None) remove a session 'nome' do dicionário de sessions. O pop('nome', None) indica que se o 1º parâmetro chave não 
        estiver no dicionário e não existir um 2º parâmetro, um KeyError será criado. Caso exista o 2º parâmetro, esse será retornado 
        impedindo que um KeyError seja criado, porém o conteúdo da session do 1º parâmetro continuará a existir.
    '''

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
