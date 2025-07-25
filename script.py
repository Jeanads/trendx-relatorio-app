# 🔧 Script de Preparação para Deploy
# Execute este script antes de fazer deploy para garantir compatibilidade

import os
import subprocess
import sys

def criar_requirements():
    """Cria requirements.txt atualizado"""
    print("📦 Criando requirements.txt...")
    
    requirements = """streamlit==1.28.1
plotly==5.17.0
pandas==2.1.3
requests==2.31.0
python-multipart==0.0.6
numpy==1.24.3
sqlite3"""
    
    with open('requirements.txt', 'w') as f:
        f.write(requirements)
    
    print("✅ requirements.txt criado!")

def criar_procfile():
    """Cria Procfile para Heroku/Railway"""
    print("📝 Criando Procfile...")
    
    with open('Procfile', 'w') as f:
        f.write('web: streamlit run dashboard.py --server.port=$PORT --server.address=0.0.0.0\n')
    
    print("✅ Procfile criado!")

def criar_setup_sh():
    """Cria setup.sh para algumas plataformas"""
    print("🛠️ Criando setup.sh...")
    
    setup_content = """mkdir -p ~/.streamlit/

echo "\\
[general]\\n\\
email = \\"your-email@domain.com\\"\\n\\
" > ~/.streamlit/credentials.toml

echo "\\
[server]\\n\\
headless = true\\n\\
enableCORS=false\\n\\
port = $PORT\\n\\
" > ~/.streamlit/config.toml
"""
    
    with open('setup.sh', 'w') as f:
        f.write(setup_content)
    
    # Dar permissão de execução
    os.chmod('setup.sh', 0o755)
    
    print("✅ setup.sh criado!")

def modificar_dashboard():
    """Modifica dashboard.py para compatibilidade com deploy"""
    print("🔧 Verificando dashboard.py...")
    
    # Ler o arquivo atual
    with open('dashboard.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar se já tem as modificações
    if 'STREAMLIT_SERVER_PORT' in content:
        print("✅ dashboard.py já está configurado para deploy!")
        return
    
    # Adicionar configurações de produção no início
    production_config = '''import os

# ========== CONFIGURAÇÃO PARA PRODUÇÃO ==========
# Detecta se está rodando em ambiente de deploy
if os.getenv('STREAMLIT_SERVER_PORT') or os.getenv('PORT'):
    # Configurações para deploy
    os.environ['STREAMLIT_SERVER_PORT'] = os.getenv('PORT', '8501')
    os.environ['STREAMLIT_SERVER_ADDRESS'] = '0.0.0.0'
    os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
    os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'

'''
    
    # Inserir no início, depois dos imports principais
    import_section = content.split('\n\n')[0]  # Primeira seção de imports
    rest_of_code = content[len(import_section):]
    
    new_content = import_section + '\n\n' + production_config + rest_of_code
    
    # Backup do arquivo original
    with open('dashboard_backup.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Escrever nova versão
    with open('dashboard.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ dashboard.py modificado para deploy!")
    print("📁 Backup salvo como dashboard_backup.py")

def verificar_banco():
    """Verifica o banco de dados"""
    print("🗄️ Verificando banco de dados...")
    
    if os.path.exists('trendx_bot.db'):
        size = os.path.getsize('trendx_bot.db') / (1024 * 1024)  # MB
        print(f"✅ Banco encontrado: {size:.1f} MB")
        
        if size > 100:
            print("⚠️ ATENÇÃO: Banco muito grande (>100MB)")
            print("💡 Considere:")
            print("   1. Limpar dados antigos")
            print("   2. Migrar para PostgreSQL")
            print("   3. Usar banco online")
        else:
            print("✅ Tamanho adequado para deploy!")
    else:
        print("❌ Banco não encontrado!")
        print("💡 Certifique-se que trendx_bot.db está na pasta")

def criar_readme():
    """Cria README.md"""
    print("📖 Criando README.md...")
    
    readme_content = """# 📈 TrendX Analytics Dashboard

Dashboard completo para análise de métricas de redes sociais.

## 🚀 Features

- 📊 Dashboard executivo completo
- 🏆 Rankings com fórmulas reais das redes sociais
- 👤 Análise individual de usuários
- 🎬 Análise completa de vídeos com links
- 💡 Insights personalizados

## 🔧 Como rodar localmente

```bash
pip install -r requirements.txt
streamlit run dashboard.py
```

## 📱 Versão Online

[Link do Dashboard](https://seu-link-aqui.streamlit.app)

## 🛠️ Tecnologias

- Streamlit
- Plotly
- Pandas
- SQLite

## 📊 Métricas Calculadas

### Taxa de Engajamento por Plataforma:
- **TikTok**: `(Curtidas + Comentários + Shares) / Views × 100`
- **YouTube**: `(Curtidas + Comentários) / Views × 100`  
- **Instagram**: `(Curtidas + Comentários + Shares) / Views × 100`

### Score de Performance (0-100):
- 50% Taxa de Engajamento
- 30% Volume de Alcance
- 20% Consistência
"""
    
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print("✅ README.md criado!")

def testar_local():
    """Testa se funciona localmente"""
    print("🧪 Testando funcionamento local...")
    
    try:
        # Tentar importar as principais dependências
        import streamlit as st
        import plotly.express as px
        import pandas as pd
        import sqlite3
        
        print("✅ Todas as dependências OK!")
        
        # Verificar se o script roda sem erros de sintaxe
        with open('dashboard.py', 'r', encoding='utf-8') as f:
            code = f.read()
        
        compile(code, 'dashboard.py', 'exec')
        print("✅ Código sem erros de sintaxe!")
        
        print("🚀 Recomendação: Teste com 'streamlit run dashboard.py' antes do deploy")
        
    except ImportError as e:
        print(f"❌ Dependência faltando: {e}")
        print("💡 Execute: pip install -r requirements.txt")
    except SyntaxError as e:
        print(f"❌ Erro de sintaxe no código: {e}")
    except Exception as e:
        print(f"⚠️ Aviso: {e}")

def criar_gitignore():
    """Cria .gitignore apropriado"""
    print("📝 Criando .gitignore...")
    
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/
env/
.venv/

# IDEs
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# Backup files
*_backup.py

# Temporary files
*.tmp
*.temp
"""
    
    with open('.gitignore', 'w') as f:
        f.write(gitignore_content)
    
    print("✅ .gitignore criado!")

def main():
    """Função principal"""
    print("🚀 PREPARANDO PROJETO PARA DEPLOY")
    print("=" * 50)
    
    # Verificar se estamos na pasta certa
    if not os.path.exists('dashboard.py'):
        print("❌ Erro: dashboard.py não encontrado!")
        print("💡 Execute este script na pasta do projeto")
        return
    
    # Executar todas as preparações
    criar_requirements()
    criar_procfile()
    criar_setup_sh()
    modificar_dashboard()
    verificar_banco()
    criar_readme()
    criar_gitignore()
    testar_local()
    
    print("\n🎉 PREPARAÇÃO CONCLUÍDA!")
    print("=" * 50)
    print("📋 PRÓXIMOS PASSOS:")
    print("1. ✅ Teste local: streamlit run dashboard.py")
    print("2. 📁 Commit no GitHub:")
    print("   git add .")
    print("   git commit -m 'Preparar para deploy'")
    print("   git push")
    print("3. 🚀 Deploy em uma das plataformas:")
    print("   - Streamlit Community Cloud (RECOMENDADO)")
    print("   - Render")
    print("   - Railway")
    print("\n🔗 Guia completo de deploy criado!")

if __name__ == "__main__":
    main()