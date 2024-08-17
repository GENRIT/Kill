import telebot
from github import Github
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import re
import base64

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

BOT_TOKEN = '7416204500:AAHfx67vXqCgcrwpp2uzoXEIvC2fwiQSp5o'
bot = telebot.TeleBot(BOT_TOKEN)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    github_token = db.Column(db.String(100), nullable=False)
    telegram_id = db.Column(db.Integer, unique=True, nullable=True)

with app.app_context():
    db.create_all()

@bot.message_handler(commands=['start'])
def start(message):
    user = User.query.filter_by(telegram_id=message.from_user.id).first()
    if user:
        bot.reply_to(message, f"Welcome back, {user.username}! Your GitHub bot is ready to use. Type /help for available commands.")
    else:
        bot.reply_to(message, "Welcome! Please register on our website to use the GitHub bot. After registration, use /link command to connect your account.")

@bot.message_handler(commands=['link'])
def link_account(message):
    args = message.text.split()[1:]
    if len(args) != 2:
        bot.reply_to(message, "Usage: /link <username> <password>")
        return

    username, password = args
    user = User.query.filter_by(username=username).first()
    if user and user.password == password:
        user.telegram_id = message.from_user.id
        db.session.commit()
        bot.reply_to(message, f"Account linked successfully! Welcome, {username}. Type /help for available commands.")
    else:
        bot.reply_to(message, "Invalid username or password.")

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
Available commands:
/repos - List your GitHub repositories
/issues <repo_name> - List open issues in a repository
/create_issue <repo_name> <title> <body> - Create a new issue
/branches <repo_name> - List branches in a repository
/commits <repo_name> <branch_name> - List recent commits in a branch
/file <repo_name> <file_path> - View contents of a file
/search <query> - Search your repositories
    """
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['repos'])
def list_repos(message):
    user = User.query.filter_by(telegram_id=message.from_user.id).first()
    if not user:
        bot.reply_to(message, "Please link your account first using /link <username> <password>")
        return

    g = Github(user.github_token)
    repos = g.get_user().get_repos()
    repo_list = [f"• {repo.name}" for repo in repos]
    response = "Your repositories:\n" + "\n".join(repo_list)
    bot.reply_to(message, response)

@bot.message_handler(commands=['issues'])
def list_issues(message):
    user = User.query.filter_by(telegram_id=message.from_user.id).first()
    if not user:
        bot.reply_to(message, "Please link your account first using /link <username> <password>")
        return

    args = message.text.split()[1:]
    if len(args) != 1:
        bot.reply_to(message, "Usage: /issues <repo_name>")
        return

    repo_name = args[0]
    g = Github(user.github_token)
    try:
        repo = g.get_user().get_repo(repo_name)
        issues = repo.get_issues(state='open')
        issue_list = [f"#{issue.number}: {issue.title}" for issue in issues]
        response = f"Open issues in {repo_name}:\n" + "\n".join(issue_list) if issue_list else f"No open issues in {repo_name}"
        bot.reply_to(message, response)
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

@bot.message_handler(commands=['create_issue'])
def create_issue(message):
    user = User.query.filter_by(telegram_id=message.from_user.id).first()
    if not user:
        bot.reply_to(message, "Please link your account first using /link <username> <password>")
        return

    args = message.text.split(maxsplit=3)[1:]
    if len(args) != 3:
        bot.reply_to(message, "Usage: /create_issue <repo_name> <title> <body>")
        return

    repo_name, title, body = args
    g = Github(user.github_token)
    try:
        repo = g.get_user().get_repo(repo_name)
        issue = repo.create_issue(title=title, body=body)
        bot.reply_to(message, f"Issue created successfully. Issue #{issue.number}: {issue.title}")
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

@bot.message_handler(commands=['branches'])
def list_branches(message):
    user = User.query.filter_by(telegram_id=message.from_user.id).first()
    if not user:
        bot.reply_to(message, "Please link your account first using /link <username> <password>")
        return

    args = message.text.split()[1:]
    if len(args) != 1:
        bot.reply_to(message, "Usage: /branches <repo_name>")
        return

    repo_name = args[0]
    g = Github(user.github_token)
    try:
        repo = g.get_user().get_repo(repo_name)
        branches = repo.get_branches()
        branch_list = [f"• {branch.name}" for branch in branches]
        response = f"Branches in {repo_name}:\n" + "\n".join(branch_list)
        bot.reply_to(message, response)
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

@bot.message_handler(commands=['commits'])
def list_commits(message):
    user = User.query.filter_by(telegram_id=message.from_user.id).first()
    if not user:
        bot.reply_to(message, "Please link your account first using /link <username> <password>")
        return

    args = message.text.split()[1:]
    if len(args) != 2:
        bot.reply_to(message, "Usage: /commits <repo_name> <branch_name>")
        return

    repo_name, branch_name = args
    g = Github(user.github_token)
    try:
        repo = g.get_user().get_repo(repo_name)
        commits = repo.get_commits(sha=branch_name)
        commit_list = [f"• {commit.sha[:7]}: {commit.commit.message.split()[0]}" for commit in commits[:5]]
        response = f"Recent commits in {repo_name}/{branch_name}:\n" + "\n".join(commit_list)
        bot.reply_to(message, response)
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

@bot.message_handler(commands=['file'])
def view_file(message):
    user = User.query.filter_by(telegram_id=message.from_user.id).first()
    if not user:
        bot.reply_to(message, "Please link your account first using /link <username> <password>")
        return

    args = message.text.split(maxsplit=2)[1:]
    if len(args) != 2:
        bot.reply_to(message, "Usage: /file <repo_name> <file_path>")
        return

    repo_name, file_path = args
    g = Github(user.github_token)
    try:
        repo = g.get_user().get_repo(repo_name)
        content = repo.get_contents(file_path)
        file_content = base64.b64decode(content.content).decode('utf-8')
        response = f"Contents of {file_path}:\n\n```\n{file_content[:1000]}```"
        if len(file_content) > 1000:
            response += "\n... (truncated)"
        bot.reply_to(message, response, parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

@bot.message_handler(commands=['search'])
def search_repos(message):
    user = User.query.filter_by(telegram_id=message.from_user.id).first()
    if not user:
        bot.reply_to(message, "Please link your account first using /link <username> <password>")
        return

    args = message.text.split(maxsplit=1)[1:]
    if len(args) != 1:
        bot.reply_to(message, "Usage: /search <query>")
        return

    query = args[0]
    g = Github(user.github_token)
    try:
        repos = g.search_repositories(query=f"user:{g.get_user().login} {query}")
        repo_list = [f"• {repo.name}: {repo.description}" for repo in repos[:5]]
        response = f"Search results for '{query}':\n" + "\n".join(repo_list)
        if not repo_list:
            response = f"No repositories found matching '{query}'"
        bot.reply_to(message, response)
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    bot.reply_to(message, "I don't understand that command. Type /help for a list of available commands.")

if __name__ == '__main__':
    bot.polling()