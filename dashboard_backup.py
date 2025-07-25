import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from datetime import datetime, timedelta
import numpy as np
import json

# ========== CONFIGURAÇÃO DA PÁGINA ==========
st.set_page_config(
    page_title="TrendX Analytics - Versão Completa",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== CSS AVANÇADO ==========
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    
    .metric-card {
        background: linear-gradient(145deg, #ffffff, #f8f9fa);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e9ecef;
        box-shadow: 0 4px 16px rgba(0,0,0,0.08);
        margin: 0.5rem 0;
        transition: transform 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.12);
    }
    
    .ranking-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 5px solid #667eea;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        transition: all 0.2s ease;
    }
    
    .ranking-card:hover {
        transform: translateX(5px);
        box-shadow: 0 6px 16px rgba(0,0,0,0.12);
    }
    
    .video-card {
        background: linear-gradient(145deg, #ffffff, #f8f9fa);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e9ecef;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    
    .zero-user-card {
        background: linear-gradient(145deg, #fff3cd, #fef3cd);
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #ffc107;
        margin: 0.5rem 0;
        opacity: 0.8;
    }
    
    .insight-box {
        background: linear-gradient(145deg, #e3f2fd, #f3e5f5);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 5px solid #2196f3;
        margin: 1rem 0;
    }
    
    .warning-box {
        background: linear-gradient(145deg, #fff3e0, #fce4ec);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 5px solid #ff9800;
        margin: 1rem 0;
    }
    
    .success-box {
        background: linear-gradient(145deg, #e8f5e8, #f1f8e9);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 5px solid #4caf50;
        margin: 1rem 0;
    }
    
    .stats-box {
        background: linear-gradient(145deg, #f8f9fa, #e9ecef);
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #dee2e6;
        margin: 0.5rem 0;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: linear-gradient(145deg, #f8f9fa, #e9ecef);
        border-radius: 10px;
        padding: 12px 20px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ========== CONFIGURAÇÕES ==========
DB_PATH = "trendx_bot.db"

# ========== FUNÇÕES UTILITÁRIAS AVANÇADAS ==========
def converter_para_numerico_seguro(series, valor_padrao=0):
    """Converte uma série para numérico de forma segura"""
    try:
        return pd.to_numeric(series, errors='coerce').fillna(valor_padrao)
    except:
        return pd.Series([valor_padrao] * len(series), index=series.index)

def formatar_numero(num):
    """Formatar números para exibição"""
    try:
        if pd.isna(num) or num == 0:
            return "0"
        
        # Converter para float se for categórico ou string
        if isinstance(num, (str, pd.Categorical)):
            try:
                num = float(num)
            except:
                return "0"
        
        if num >= 1000000000:
            return f"{num/1000000000:.1f}B"
        elif num >= 1000000:
            return f"{num/1000000:.1f}M"
        elif num >= 1000:
            return f"{num/1000:.1f}K"
        else:
            return f"{int(num):,}"
    except:
        return "0"

def calcular_engajamento_por_plataforma(views, likes, comments, shares, platform):
    """Calcula engajamento usando as fórmulas oficiais de cada rede social"""
    if views == 0:
        return 0
    
    if platform.lower() == 'tiktok':
        # TikTok: (Curtidas + Comentários + Compartilhamentos) / Views × 100
        # TikTok considera todas as interações igualmente
        engajamento = ((likes + comments + shares) / views) * 100
    
    elif platform.lower() == 'youtube':
        # YouTube: (Curtidas + Comentários) / Views × 100
        # YouTube não conta shares da mesma forma
        engajamento = ((likes + comments) / views) * 100
    
    elif platform.lower() == 'instagram':
        # Instagram: (Curtidas + Comentários + Compartilhamentos) / Alcance × 100
        # Instagram usa alcance, mas como temos views, usamos views
        engajamento = ((likes + comments + shares) / views) * 100
    
    else:
        # Fórmula geral para outras plataformas
        engajamento = ((likes + comments + shares) / views) * 100
    
    return round(engajamento, 2)

def calcular_score_performance_real(views, likes, comments, shares, videos, platform_principal=None):
    """Calcula score baseado nas métricas reais das redes sociais"""
    if views == 0 or videos == 0:
        return 0
    
    # 1. Taxa de Engajamento Real (50% do score)
    if platform_principal:
        taxa_engajamento = calcular_engajamento_por_plataforma(views, likes, comments, shares, platform_principal)
    else:
        # Fórmula geral se não soubermos a plataforma principal
        taxa_engajamento = ((likes + comments + shares) / views) * 100
    
    # Normalizar taxa de engajamento para pontuação (0-50 pontos)
    # Taxa > 10% = pontuação máxima (50 pontos)
    score_engajamento = min(taxa_engajamento * 5, 50)
    
    # 2. Volume de Alcance (30% do score)
    # Baseado em views totais, mas com escala logarítmica
    score_volume = min(np.log1p(views) * 3, 30)
    
    # 3. Frequência/Consistência (20% do score)
    # Views por vídeo - mede se cada vídeo tem performance boa
    views_por_video = views / videos
    score_consistencia = min(views_por_video * 0.002, 20)
    
    total_score = score_engajamento + score_volume + score_consistencia
    return min(round(total_score, 1), 100)

def determinar_plataforma_principal(tiktok_views, youtube_views, instagram_views):
    """Determina qual é a plataforma principal do usuário"""
    plataformas = {
        'tiktok': tiktok_views,
        'youtube': youtube_views, 
        'instagram': instagram_views
    }
    
    # Retorna a plataforma com mais views
    plataforma_principal = max(plataformas.items(), key=lambda x: x[1])
    return plataforma_principal[0] if plataforma_principal[1] > 0 else None

def obter_categoria_performance(score):
    """Retorna categoria baseada no score"""
    if score >= 80:
        return "🏆 Elite", "#ffd700"
    elif score >= 60:
        return "🥇 Expert", "#c0c0c0"
    elif score >= 40:
        return "🥈 Avançado", "#cd7f32"
    elif score >= 20:
        return "🥉 Intermediário", "#4caf50"
    elif score > 0:
        return "🌱 Iniciante", "#ff9800"
    else:
        return "😴 Inativo", "#6c757d"

def conectar_banco():
    """Conecta com o banco de dados"""
    if not os.path.exists(DB_PATH):
        st.error(f"❌ Banco de dados não encontrado: {DB_PATH}")
        return None
    return sqlite3.connect(DB_PATH)

@st.cache_data(ttl=300)
def carregar_dados_usuarios_completo():
    """Carrega TODOS os usuários (incluindo com zeros)"""
    conn = conectar_banco()
    if not conn:
        return pd.DataFrame()
    
    try:
        query = """
        SELECT 
            user_id,
            discord_username,
            COALESCE(total_videos, 0) as total_videos,
            COALESCE(total_views, 0) as total_views,
            COALESCE(total_likes, 0) as total_likes,
            COALESCE(total_comments, 0) as total_comments,
            COALESCE(total_shares, 0) as total_shares,
            COALESCE(tiktok_views, 0) as tiktok_views,
            COALESCE(tiktok_videos, 0) as tiktok_videos,
            COALESCE(youtube_views, 0) as youtube_views,
            COALESCE(youtube_videos, 0) as youtube_videos,
            COALESCE(instagram_views, 0) as instagram_views,
            COALESCE(instagram_videos, 0) as instagram_videos,
            updated_at
        FROM cached_stats 
        WHERE discord_username IS NOT NULL 
        AND discord_username != ''
        ORDER BY total_views DESC
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            return df
        
        # Converter todas as colunas numéricas de forma segura
        numeric_columns = ['total_videos', 'total_views', 'total_likes', 'total_comments', 'total_shares',
                          'tiktok_views', 'tiktok_videos', 'youtube_views', 'youtube_videos', 
                          'instagram_views', 'instagram_videos']
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = converter_para_numerico_seguro(df[col], 0)
        
        # Calcular métricas avançadas
        df['total_interactions'] = df['total_likes'] + df['total_comments'] + df['total_shares']
        
        # Garantir que não há divisão por zero e converter para float
        df['total_views'] = pd.to_numeric(df['total_views'], errors='coerce').fillna(0)
        df['total_videos'] = pd.to_numeric(df['total_videos'], errors='coerce').fillna(0)
        df['total_interactions'] = pd.to_numeric(df['total_interactions'], errors='coerce').fillna(0)
        
        # Calcular taxa de engajamento por plataforma (usando fórmulas reais)
        df['plataforma_principal'] = df.apply(
            lambda x: determinar_plataforma_principal(
                x['tiktok_views'], x['youtube_views'], x['instagram_views']
            ), axis=1
        )
        
        # Taxa de engajamento usando fórmulas reais das redes sociais
        df['taxa_engajamento'] = df.apply(
            lambda x: calcular_engajamento_por_plataforma(
                x['total_views'], x['total_likes'], x['total_comments'], 
                x['total_shares'], x['plataforma_principal'] or 'geral'
            ), axis=1
        )
        
        # Score de performance usando métricas reais
        df['score_performance'] = df.apply(
            lambda x: calcular_score_performance_real(
                x['total_views'], x['total_likes'], x['total_comments'], 
                x['total_shares'], x['total_videos'], x['plataforma_principal']
            ), axis=1
        ).round(1)
        
        # Métricas complementares
        df['media_views_por_video'] = (df['total_views'] / df['total_videos'].replace(0, 1)).round(0)
        df['media_likes_por_video'] = (df['total_likes'] / df['total_videos'].replace(0, 1)).round(0)
        df['media_comments_por_video'] = (df['total_comments'] / df['total_videos'].replace(0, 1)).round(2)
        
        # Categoria de performance
        df[['categoria_performance', 'cor_categoria']] = df['score_performance'].apply(
            lambda x: pd.Series(obter_categoria_performance(x))
        )
        
        # Rankings (só para usuários com dados)
        df_ativo = df[df['total_views'] > 0]
        if not df_ativo.empty:
            df.loc[df['total_views'] > 0, 'rank_views'] = df_ativo['total_views'].rank(ascending=False, method='min').astype(int)
            df.loc[df['total_likes'] > 0, 'rank_likes'] = df_ativo['total_likes'].rank(ascending=False, method='min').astype(int)
            df.loc[df['taxa_engajamento'] > 0, 'rank_engajamento'] = df_ativo['taxa_engajamento'].rank(ascending=False, method='min').astype(int)
            df.loc[df['score_performance'] > 0, 'rank_performance'] = df_ativo['score_performance'].rank(ascending=False, method='min').astype(int)
        
        # Preencher NaN dos rankings com 0
        df[['rank_views', 'rank_likes', 'rank_engajamento', 'rank_performance']] = df[['rank_views', 'rank_likes', 'rank_engajamento', 'rank_performance']].fillna(0).astype(int)
        
        # Análise de consistência
        df['consistencia'] = np.where(
            df['total_videos'] > 5,
            np.where(df['taxa_engajamento'] > df['taxa_engajamento'].median(), "Alta", "Média"),
            np.where(df['total_videos'] > 0, "Baixa", "Sem dados")
        )
        
        # Status do usuário
        df['status_usuario'] = np.where(
            df['total_views'] == 0,
            "🔴 Inativo",
            np.where(
                df['total_views'] >= df['total_views'].quantile(0.75),
                "🟢 Muito Ativo",
                np.where(
                    df['total_views'] >= df['total_views'].median(),
                    "🟡 Ativo",
                    "🟠 Pouco Ativo"
                )
            )
        )
        
        # Potencial de crescimento
        df['potencial_crescimento'] = np.where(
            df['total_views'] == 0,
            "Sem dados",
            np.where(
                (df['taxa_engajamento'] > df['taxa_engajamento'].quantile(0.75)) & 
                (df['total_videos'] < df['total_videos'].quantile(0.5)),
                "Alto", 
                np.where(df['taxa_engajamento'] > df['taxa_engajamento'].median(), "Médio", "Baixo")
            )
        )
        
        return df
        
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        if conn:
            conn.close()
        return pd.DataFrame()

@st.cache_data(ttl=300)
def carregar_videos_completo():
    """Carrega TODOS os vídeos do banco (sem limite)"""
    conn = conectar_banco()
    if not conn:
        return pd.DataFrame()
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='valid_videos'")
        if not cursor.fetchone():
            conn.close()
            return pd.DataFrame()
        
        # Primeiro, contar quantos vídeos existem
        cursor.execute("SELECT COUNT(*) FROM valid_videos")
        total_videos = cursor.fetchone()[0]
        
        # Query sem LIMIT para carregar todos
        query = """
        SELECT 
            v.*,
            cs.discord_username
        FROM valid_videos v
        LEFT JOIN cached_stats cs ON v.user_id = cs.user_id
        WHERE cs.discord_username IS NOT NULL
        ORDER BY v.id DESC
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if not df.empty:
            # Converter colunas numéricas de forma segura
            numeric_cols = ['views', 'likes', 'comments', 'shares']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = converter_para_numerico_seguro(df[col], 0)
            
            # Métricas avançadas por vídeo usando fórmulas reais
            if 'views' in df.columns and 'likes' in df.columns:
                df['interactions'] = df['likes'] + df['comments'] + df['shares']
                
                # Taxa de engajamento usando fórmula da plataforma específica
                df['engagement_rate'] = df.apply(
                    lambda x: calcular_engajamento_por_plataforma(
                        x['views'], x['likes'], x['comments'], 
                        x['shares'], x.get('platform', 'geral')
                    ), axis=1
                )
                
                # Score do vídeo simplificado
                df['video_score'] = (
                    df['engagement_rate'] * 0.6 +  # 60% engajamento
                    np.log1p(df['views']) * 0.4     # 40% alcance
                ).round(2)
                
                # Categoria do vídeo (convertida para string)
                try:
                    df['categoria_video'] = pd.cut(
                        df['engagement_rate'],
                        bins=[0, 1, 3, 6, 10, 100],
                        labels=['🔴 Baixo', '🟡 Regular', '🟢 Bom', '🔵 Muito Bom', '🟣 Excepcional'],
                        include_lowest=True
                    ).astype(str)
                except:
                    # Fallback se pd.cut falhar
                    df['categoria_video'] = '📊 Sem categoria'
                
                # Status do link
                df['tem_link'] = df['url'].notna() & (df['url'] != '') & (df['url'].str.len() > 10)
            
            # Adicionar informação sobre o total
            st.session_state['total_videos_banco'] = total_videos
            st.session_state['videos_carregados'] = len(df)
        
        return df
        
    except Exception as e:
        st.error(f"Erro ao carregar vídeos: {str(e)}")
        if conn:
            conn.close()
        return pd.DataFrame()

def gerar_insights_usuario(usuario_data, df_usuarios):
    """Gera insights personalizados para um usuário"""
    insights = []
    recomendacoes = []
    
    # Verificar se é usuário inativo
    if usuario_data['total_views'] == 0:
        insights.append("😴 Usuário inativo - Nenhuma visualização registrada")
        recomendacoes.append("🚀 Comece publicando conteúdo nas plataformas disponíveis")
        recomendacoes.append("📅 Estabeleça uma rotina de postagem consistente")
        return insights, recomendacoes
    
    # Análise de posição (só para usuários ativos)
    usuarios_ativos = df_usuarios[df_usuarios['total_views'] > 0]
    total_usuarios_ativos = len(usuarios_ativos)
    rank_views = usuario_data['rank_views']
    rank_performance = usuario_data['rank_performance']
    
    # Insights de posição
    if rank_views <= total_usuarios_ativos * 0.1:
        insights.append("🏆 Você está no TOP 10% em visualizações!")
    elif rank_views <= total_usuarios_ativos * 0.25:
        insights.append("🥇 Você está no TOP 25% em visualizações!")
    
    if rank_performance <= total_usuarios_ativos * 0.1:
        insights.append("⭐ Performance excepcional - TOP 10% geral!")
    
    # Análise de engajamento
    taxa = usuario_data['taxa_engajamento']
    media_taxa = usuarios_ativos['taxa_engajamento'].mean()
    
    if taxa > media_taxa * 2:
        insights.append("🚀 Sua taxa de engajamento é DUPLA da média!")
        recomendacoes.append("📈 Aumente a frequência de posts para maximizar o alcance")
    elif taxa > media_taxa:
        insights.append("✅ Taxa de engajamento acima da média")
        recomendacoes.append("🎯 Analise seus melhores vídeos para replicar o sucesso")
    else:
        insights.append("📊 Há oportunidade para melhorar o engajamento")
        recomendacoes.append("💡 Use mais CTAs e interaja ativamente com comentários")
    
    # Análise de volume
    videos = usuario_data['total_videos']
    if videos > 100:
        insights.append("🎥 Criador muito ativo com grande volume de conteúdo")
        if taxa < media_taxa:
            recomendacoes.append("🎯 Foque na qualidade - menos posts, mais cuidado na produção")
    elif videos < 20:
        insights.append("🌱 Espaço para crescer com mais conteúdo")
        recomendacoes.append("📅 Estabeleça uma rotina de postagem consistente")
    
    # Análise de plataformas
    plataformas_ativas = []
    if usuario_data.get('tiktok_views', 0) > 0:
        plataformas_ativas.append('TikTok')
    if usuario_data.get('youtube_views', 0) > 0:
        plataformas_ativas.append('YouTube')
    if usuario_data.get('instagram_views', 0) > 0:
        plataformas_ativas.append('Instagram')
    
    if len(plataformas_ativas) == 1:
        recomendacoes.append(f"📱 Considere expandir além do {plataformas_ativas[0]} para diversificar")
    elif len(plataformas_ativas) >= 2:
        insights.append(f"🎯 Boa diversificação: ativo em {len(plataformas_ativas)} plataformas")
    
    return insights, recomendacoes

# ========== PÁGINAS AVANÇADAS ==========
def pagina_dashboard_executivo(df_usuarios):
    """Dashboard executivo com visão geral completa"""
    st.markdown('<div class="main-header"><h1>📊 Dashboard Executivo Completo</h1><p>Visão Geral de TODOS os Usuários</p></div>', unsafe_allow_html=True)
    
    if df_usuarios.empty:
        st.warning("⚠️ Nenhum dado disponível")
        return
    
    # Estatísticas gerais
    total_usuarios = len(df_usuarios)
    usuarios_ativos = len(df_usuarios[df_usuarios['total_views'] > 0])
    usuarios_inativos = total_usuarios - usuarios_ativos
    
    # KPIs principais
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #667eea; margin: 0;">👥 Total</h3>
            <h2 style="margin: 0.5rem 0;">{total_usuarios}</h2>
            <p style="margin: 0; color: #666;">Usuários cadastrados</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #28a745; margin: 0;">🟢 Ativos</h3>
            <h2 style="margin: 0.5rem 0;">{usuarios_ativos}</h2>
            <p style="margin: 0; color: #666;">{(usuarios_ativos/total_usuarios*100):.1f}% do total</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #dc3545; margin: 0;">🔴 Inativos</h3>
            <h2 style="margin: 0.5rem 0;">{usuarios_inativos}</h2>
            <p style="margin: 0; color: #666;">{(usuarios_inativos/total_usuarios*100):.1f}% do total</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        total_videos = df_usuarios['total_videos'].sum()
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #667eea; margin: 0;">🎥 Vídeos</h3>
            <h2 style="margin: 0.5rem 0;">{formatar_numero(total_videos)}</h2>
            <p style="margin: 0; color: #666;">Total publicados</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        total_views = df_usuarios['total_views'].sum()
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #667eea; margin: 0;">👁️ Views</h3>
            <h2 style="margin: 0.5rem 0;">{formatar_numero(total_views)}</h2>
            <p style="margin: 0; color: #666;">Total alcançadas</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col6:
        usuarios_ativos_df = df_usuarios[df_usuarios['total_views'] > 0]
        engagement_medio = usuarios_ativos_df['taxa_engajamento'].mean() if not usuarios_ativos_df.empty else 0
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #667eea; margin: 0;">📈 Engajamento</h3>
            <h2 style="margin: 0.5rem 0;">{engagement_medio:.1f}%</h2>
            <p style="margin: 0; color: #666;">Média usuários ativos</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Análise de distribuição
    col1, col2 = st.columns(2)
    
    with col1:
        # Status dos usuários
        status_counts = df_usuarios['status_usuario'].value_counts()
        
        fig_status = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title="📊 Distribuição por Status de Atividade",
            color_discrete_sequence=['#28a745', '#ffc107', '#fd7e14', '#dc3545']
        )
        fig_status.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_status, use_container_width=True)
    
    with col2:
        # Distribuição por categoria (só usuários ativos)
        usuarios_ativos_df = df_usuarios[df_usuarios['total_views'] > 0]
        if not usuarios_ativos_df.empty:
            dist_categoria = usuarios_ativos_df['categoria_performance'].value_counts()
            
            fig_cat = px.pie(
                values=dist_categoria.values,
                names=dist_categoria.index,
                title="🏆 Distribuição por Performance (Usuários Ativos)",
                color_discrete_sequence=['#ffd700', '#c0c0c0', '#cd7f32', '#4caf50', '#ff9800']
            )
            fig_cat.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_cat, use_container_width=True)
        else:
            st.info("📊 Nenhum usuário ativo para análise de performance")
    
    st.divider()
    
    # Top performers e usuários inativos
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏆 Top 10 Performers")
        if not usuarios_ativos_df.empty:
            top_performers = usuarios_ativos_df.nlargest(10, 'score_performance')
            
            for i, (_, user) in enumerate(top_performers.iterrows(), 1):
                categoria, cor = user['categoria_performance'], user['cor_categoria']
                st.markdown(f"""
                <div style="background: white; padding: 0.8rem; border-radius: 8px; 
                            border-left: 4px solid {cor}; margin: 0.3rem 0;">
                    <strong>#{i} {user['discord_username']}</strong><br>
                    <small>{categoria} - Score: {user['score_performance']:.1f}</small><br>
                    <small>👁️ {formatar_numero(user['total_views'])} views | 🎥 {user['total_videos']} vídeos</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("📊 Nenhum usuário ativo encontrado")
    
    with col2:
        st.subheader("😴 Usuários Inativos")
        usuarios_inativos_df = df_usuarios[df_usuarios['total_views'] == 0]
        
        if not usuarios_inativos_df.empty:
            st.warning(f"⚠️ {len(usuarios_inativos_df)} usuários sem visualizações")
            
            # Mostrar alguns usuários inativos
            for i, (_, user) in enumerate(usuarios_inativos_df.head(10).iterrows(), 1):
                st.markdown(f"""
                <div class="zero-user-card">
                    <strong>{user['discord_username']}</strong><br>
                    <small>😴 Sem atividade registrada</small>
                </div>
                """, unsafe_allow_html=True)
            
            if len(usuarios_inativos_df) > 10:
                st.info(f"➕ E mais {len(usuarios_inativos_df) - 10} usuários inativos...")
        else:
            st.success("🎉 Todos os usuários têm atividade!")

def pagina_rankings_completos(df_usuarios):
    """Rankings completos com controle de visualização"""
    st.markdown('<div class="main-header"><h1>🏆 Rankings Completos</h1><p>Controle Total sobre Visualizações</p></div>', unsafe_allow_html=True)
    
    if df_usuarios.empty:
        st.warning("⚠️ Nenhum dado disponível")
        return
    
    # Controles avançados
    st.subheader("🎛️ Controles de Visualização")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        incluir_inativos = st.checkbox("😴 Incluir usuários inativos", value=False, help="Mostrar usuários com 0 views")
    
    with col2:
        if incluir_inativos:
            max_usuarios = len(df_usuarios)
            opcoes_top = [10, 20, 30, 50, 100, max_usuarios]
            labels_top = [f"Top {x}" for x in opcoes_top[:-1]] + [f"Todos ({max_usuarios})"]
        else:
            usuarios_ativos = df_usuarios[df_usuarios['total_views'] > 0]
            max_usuarios = len(usuarios_ativos)
            opcoes_top = [10, 20, 30, 50, 100, max_usuarios]
            labels_top = [f"Top {x}" for x in opcoes_top[:-1]] + [f"Todos ativos ({max_usuarios})"]
        
        top_n_idx = st.selectbox("📊 Quantidade no ranking:", range(len(opcoes_top)), format_func=lambda x: labels_top[x], index=1)
        top_n = opcoes_top[top_n_idx]
    
    with col3:
        mostrar_graficos = st.checkbox("📈 Mostrar gráficos", value=True)
    
    with col4:
        formato_grafico = st.selectbox("📊 Tipo de gráfico:", ["Barras Horizontais", "Barras Verticais", "Apenas Tabela"])
    
    # Filtrar dados baseado na seleção
    if incluir_inativos:
        df_trabalho = df_usuarios.copy()
        st.info(f"📊 Mostrando dados de {len(df_trabalho)} usuários (incluindo {len(df_usuarios[df_usuarios['total_views'] == 0])} inativos)")
    else:
        df_trabalho = df_usuarios[df_usuarios['total_views'] > 0].copy()
        inativos_ocultos = len(df_usuarios) - len(df_trabalho)
        if inativos_ocultos > 0:
            st.info(f"📊 Mostrando apenas usuários ativos. {inativos_ocultos} usuários inativos ocultos.")
    
    if df_trabalho.empty:
        st.warning("⚠️ Nenhum usuário encontrado com os filtros aplicados")
        return
    
    st.divider()
    
    # Abas dos rankings
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "👁️ Mais Views", "❤️ Mais Curtidas", "📈 Melhor Engajamento", 
        "🏆 Score Performance", "📱 Por Plataforma"
    ])
    
    with tab1:
        st.subheader(f"👁️ Ranking por Visualizações")
        top_views = df_trabalho.nlargest(top_n, 'total_views')
        
        if mostrar_graficos and formato_grafico != "Apenas Tabela":
            if formato_grafico == "Barras Horizontais":
                fig = px.bar(
                    top_views,
                    x='total_views',
                    y='discord_username',
                    orientation='h',
                    title=f"Ranking por Visualizações",
                    color='total_views',
                    color_continuous_scale='Blues',
                    text='total_views'
                )
                fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
                fig.update_yaxes(categoryorder='total ascending')
                fig.update_layout(height=max(400, min(len(top_views) * 25, 800)), showlegend=False)
            else:  # Barras Verticais
                fig = px.bar(
                    top_views.head(20),  # Limit to 20 for vertical bars
                    x='discord_username',
                    y='total_views',
                    title=f"Top 20 - Visualizações",
                    color='total_views',
                    color_continuous_scale='Blues'
                )
                fig.update_xaxes(tickangle=45)
                fig.update_layout(height=600, showlegend=False)
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Tabela detalhada
        df_display = top_views[['discord_username', 'total_views', 'total_videos', 'media_views_por_video', 'status_usuario']].copy()
        
        # Adicionar indicadores visuais para usuários inativos
        if incluir_inativos:
            df_display['indicador'] = df_display.apply(
                lambda x: "😴 INATIVO" if x['total_views'] == 0 else "🟢 ATIVO", axis=1
            )
            colunas_ordem = ['indicador', 'discord_username', 'total_views', 'total_videos', 'media_views_por_video', 'status_usuario']
        else:
            colunas_ordem = ['discord_username', 'total_views', 'total_videos', 'media_views_por_video', 'status_usuario']
        
        st.dataframe(
            df_display[colunas_ordem],
            column_config={
                "indicador": "🚦 Status",
                "discord_username": "👤 Usuário",
                "total_views": st.column_config.NumberColumn("👁️ Views Totais", format="%d"),
                "total_videos": "🎥 Vídeos",
                "media_views_por_video": st.column_config.NumberColumn("📊 Média/Vídeo", format="%.0f"),
                "status_usuario": "📊 Status"
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Estatísticas adicionais
        st.markdown("#### 📈 Estatísticas do Ranking")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📊 Total Mostrado", len(top_views))
        with col2:
            st.metric("👁️ Views Totais", formatar_numero(top_views['total_views'].sum()))
        with col3:
            st.metric("🎥 Vídeos Totais", formatar_numero(top_views['total_videos'].sum()))
        with col4:
            views_ativas = top_views[top_views['total_views'] > 0]['total_views']
            st.metric("📊 Média Views", formatar_numero(views_ativas.mean()) if not views_ativas.empty else "0")
    
    with tab2:
        st.subheader(f"❤️ Ranking por Curtidas")
        top_likes = df_trabalho.nlargest(top_n, 'total_likes')
        
        if mostrar_graficos and formato_grafico != "Apenas Tabela":
            if formato_grafico == "Barras Horizontais":
                fig = px.bar(
                    top_likes,
                    x='total_likes',
                    y='discord_username',
                    orientation='h',
                    title=f"Ranking por Curtidas",
                    color='total_likes',
                    color_continuous_scale='Reds'
                )
                fig.update_yaxes(categoryorder='total ascending')
                fig.update_layout(height=max(400, min(len(top_likes) * 25, 800)), showlegend=False)
            else:
                fig = px.bar(
                    top_likes.head(20),
                    x='discord_username',
                    y='total_likes',
                    title=f"Top 20 - Curtidas",
                    color='total_likes',
                    color_continuous_scale='Reds'
                )
                fig.update_xaxes(tickangle=45)
                fig.update_layout(height=600, showlegend=False)
            
            st.plotly_chart(fig, use_container_width=True)
        
        df_display = top_likes[['discord_username', 'total_likes', 'total_views', 'media_likes_por_video', 'taxa_engajamento']].copy()
        st.dataframe(
            df_display,
            column_config={
                "discord_username": "👤 Usuário",
                "total_likes": st.column_config.NumberColumn("❤️ Curtidas", format="%d"),
                "total_views": st.column_config.NumberColumn("👁️ Views", format="%d"),
                "media_likes_por_video": st.column_config.NumberColumn("💖 Média/Vídeo", format="%.0f"),
                "taxa_engajamento": st.column_config.NumberColumn("📈 Engajamento %", format="%.2f")
            },
            hide_index=True,
            use_container_width=True
        )
    
    with tab3:
        st.subheader(f"📈 Ranking por Engajamento")
        
        # Para engajamento, filtrar apenas usuários com dados significativos
        df_engajamento = df_trabalho[df_trabalho['total_views'] >= 100] if not incluir_inativos else df_trabalho[df_trabalho['total_views'] > 0]
        
        if df_engajamento.empty:
            st.warning("⚠️ Nenhum usuário com dados suficientes para análise de engajamento")
        else:
            top_engagement = df_engajamento.nlargest(min(top_n, len(df_engajamento)), 'taxa_engajamento')
            
            if mostrar_graficos and formato_grafico != "Apenas Tabela":
                if formato_grafico == "Barras Horizontais":
                    fig = px.bar(
                        top_engagement,
                        x='taxa_engajamento',
                        y='discord_username',
                        orientation='h',
                        title=f"Ranking por Taxa de Engajamento",
                        color='taxa_engajamento',
                        color_continuous_scale='Viridis'
                    )
                    fig.update_yaxes(categoryorder='total ascending')
                    fig.update_layout(height=max(400, min(len(top_engagement) * 25, 800)), showlegend=False)
                else:
                    fig = px.bar(
                        top_engagement.head(20),
                        x='discord_username',
                        y='taxa_engajamento',
                        title=f"Top 20 - Engajamento",
                        color='taxa_engajamento',
                        color_continuous_scale='Viridis'
                    )
                    fig.update_xaxes(tickangle=45)
                    fig.update_layout(height=600, showlegend=False)
                
                st.plotly_chart(fig, use_container_width=True)
            
            df_display = top_engagement[['discord_username', 'taxa_engajamento', 'total_views', 'total_interactions', 'consistencia']].copy()
            st.dataframe(
                df_display,
                column_config={
                    "discord_username": "👤 Usuário",
                    "taxa_engajamento": st.column_config.NumberColumn("📈 Taxa %", format="%.2f"),
                    "total_views": st.column_config.NumberColumn("👁️ Views", format="%d"),
                    "total_interactions": st.column_config.NumberColumn("💬 Interações", format="%d"),
                    "consistencia": "🎯 Consistência"
                },
                hide_index=True,
                use_container_width=True
            )
    
    with tab4:
        st.subheader(f"🏆 Ranking por Score de Performance")
        top_score = df_trabalho.nlargest(top_n, 'score_performance')
        
        if mostrar_graficos and formato_grafico != "Apenas Tabela":
            if formato_grafico == "Barras Horizontais":
                fig = px.bar(
                    top_score,
                    x='score_performance',
                    y='discord_username',
                    orientation='h',
                    title=f"Ranking por Score de Performance",
                    color='score_performance',
                    color_continuous_scale='RdYlGn'
                )
                fig.update_yaxes(categoryorder='total ascending')
                fig.update_layout(height=max(400, min(len(top_score) * 25, 800)), showlegend=False)
            else:
                fig = px.bar(
                    top_score.head(20),
                    x='discord_username',
                    y='score_performance',
                    title=f"Top 20 - Performance",
                    color='score_performance',
                    color_continuous_scale='RdYlGn'
                )
                fig.update_xaxes(tickangle=45)
                fig.update_layout(height=600, showlegend=False)
            
            st.plotly_chart(fig, use_container_width=True)
        
        df_display = top_score[['discord_username', 'score_performance', 'categoria_performance', 'plataforma_principal', 'taxa_engajamento']].copy()
        
        # Formatar plataforma principal
        df_display['plataforma_principal'] = df_display['plataforma_principal'].fillna('Geral').str.title()
        
        st.dataframe(
            df_display,
            column_config={
                "discord_username": "👤 Usuário",
                "score_performance": st.column_config.NumberColumn("🏆 Score", format="%.1f"),
                "categoria_performance": "📊 Categoria", 
                "plataforma_principal": "📱 Plataforma Principal",
                "taxa_engajamento": st.column_config.NumberColumn("📈 Engajamento %", format="%.2f")
            },
            hide_index=True,
            use_container_width=True
        )
    
    with tab5:
        st.subheader("📱 Rankings por Plataforma")
        
        plat_tabs = st.tabs(["🎵 TikTok", "📺 YouTube", "📸 Instagram"])
        
        with plat_tabs[0]:  # TikTok
            tiktok_users = df_trabalho[df_trabalho['tiktok_views'] > 0]
            if not tiktok_users.empty:
                top_tiktok = tiktok_users.nlargest(min(top_n, len(tiktok_users)), 'tiktok_views')
                
                if mostrar_graficos and formato_grafico != "Apenas Tabela":
                    fig = px.bar(
                        top_tiktok,
                        x='tiktok_views',
                        y='discord_username',
                        orientation='h',
                        title="Ranking TikTok - Views",
                        color='tiktok_views',
                        color_continuous_scale='Blues'
                    )
                    fig.update_yaxes(categoryorder='total ascending')
                    fig.update_layout(height=max(400, min(len(top_tiktok) * 25, 600)), showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)
                
                st.dataframe(
                    top_tiktok[['discord_username', 'tiktok_views', 'tiktok_videos']],
                    column_config={
                        "discord_username": "👤 Usuário",
                        "tiktok_views": st.column_config.NumberColumn("🎵 TikTok Views", format="%d"),
                        "tiktok_videos": "🎥 Vídeos"
                    },
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.info("📊 Nenhum dado do TikTok encontrado")
        
        with plat_tabs[1]:  # YouTube
            youtube_users = df_trabalho[df_trabalho['youtube_views'] > 0]
            if not youtube_users.empty:
                top_youtube = youtube_users.nlargest(min(top_n, len(youtube_users)), 'youtube_views')
                
                if mostrar_graficos and formato_grafico != "Apenas Tabela":
                    fig = px.bar(
                        top_youtube,
                        x='youtube_views',
                        y='discord_username',
                        orientation='h',
                        title="Ranking YouTube - Views",
                        color='youtube_views',
                        color_continuous_scale='Reds'
                    )
                    fig.update_yaxes(categoryorder='total ascending')
                    fig.update_layout(height=max(400, min(len(top_youtube) * 25, 600)), showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)
                
                st.dataframe(
                    top_youtube[['discord_username', 'youtube_views', 'youtube_videos']],
                    column_config={
                        "discord_username": "👤 Usuário",
                        "youtube_views": st.column_config.NumberColumn("📺 YouTube Views", format="%d"),
                        "youtube_videos": "🎥 Vídeos"
                    },
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.info("📊 Nenhum dado do YouTube encontrado")
        
        with plat_tabs[2]:  # Instagram
            instagram_users = df_trabalho[df_trabalho['instagram_views'] > 0]
            if not instagram_users.empty:
                top_instagram = instagram_users.nlargest(min(top_n, len(instagram_users)), 'instagram_views')
                
                if mostrar_graficos and formato_grafico != "Apenas Tabela":
                    fig = px.bar(
                        top_instagram,
                        x='instagram_views',
                        y='discord_username',
                        orientation='h',
                        title="Ranking Instagram - Views",
                        color='instagram_views',
                        color_continuous_scale='Purples'
                    )
                    fig.update_yaxes(categoryorder='total ascending')
                    fig.update_layout(height=max(400, min(len(top_instagram) * 25, 600)), showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)
                
                st.dataframe(
                    top_instagram[['discord_username', 'instagram_views', 'instagram_videos']],
                    column_config={
                        "discord_username": "👤 Usuário",
                        "instagram_views": st.column_config.NumberColumn("📸 Instagram Views", format="%d"),
                        "instagram_videos": "🎥 Vídeos"
                    },
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.info("📊 Nenhum dado do Instagram encontrado")

def pagina_analise_usuario_avancada(df_usuarios):
    """Análise avançada individual do usuário"""
    st.markdown('<div class="main-header"><h1>👤 Análise Individual Completa</h1><p>Insights Detalhados para Qualquer Usuário</p></div>', unsafe_allow_html=True)
    
    if df_usuarios.empty:
        st.warning("⚠️ Nenhum dado disponível")
        return
    
    # Seleção do usuário com busca
    st.subheader("🔍 Seleção de Usuário")
    usuarios = sorted(df_usuarios['discord_username'].tolist())
    
    col1, col2 = st.columns([3, 1])
    with col1:
        usuario_selecionado = st.selectbox("👤 Escolha o usuário para análise:", usuarios)
    
    with col2:
        # Mostrar estatísticas de seleção
        total_usuarios = len(usuarios)
        usuarios_ativos = len(df_usuarios[df_usuarios['total_views'] > 0])
        st.metric("📊 Total de Usuários", f"{total_usuarios}")
        st.metric("🟢 Usuários Ativos", f"{usuarios_ativos}")
    
    if usuario_selecionado:
        dados_usuario = df_usuarios[df_usuarios['discord_username'] == usuario_selecionado].iloc[0]
        
        # Verificar se é usuário ativo ou inativo
        eh_inativo = dados_usuario['total_views'] == 0
        
        # Header do usuário
        if eh_inativo:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #6c757d22, #6c757d11); 
                        border: 2px solid #6c757d; color: #333; padding: 2rem; 
                        border-radius: 15px; margin: 1rem 0; text-align: center;">
                <h2>😴 {usuario_selecionado}</h2>
                <h3 style="color: #6c757d;">USUÁRIO INATIVO</h3>
                <p><strong>Status:</strong> Nenhuma atividade registrada</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            categoria, cor = dados_usuario['categoria_performance'], dados_usuario['cor_categoria']
            plataforma_principal = dados_usuario.get('plataforma_principal', 'Geral')
            plataforma_emoji = {'tiktok': '🎵', 'youtube': '📺', 'instagram': '📸'}.get(plataforma_principal, '📱')
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, {cor}22, {cor}11); 
                        border: 2px solid {cor}; color: #333; padding: 2rem; 
                        border-radius: 15px; margin: 1rem 0; text-align: center;">
                <h2>🎯 {usuario_selecionado}</h2>
                <h3 style="color: {cor};">{categoria}</h3>
                <p><strong>Score de Performance:</strong> {dados_usuario['score_performance']:.1f}/100</p>
                <p><strong>Plataforma Principal:</strong> {plataforma_emoji} {plataforma_principal.title()}</p>
                <small>Taxa calculada usando fórmula oficial do {plataforma_principal.title()}</small>
            </div>
            """, unsafe_allow_html=True)
        
        # Métricas principais
        if eh_inativo:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("""
                <div class="stats-box">
                    <h4>😴 Status</h4>
                    <p>Usuário Inativo</p>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown("""
                <div class="stats-box">
                    <h4>📊 Dados</h4>
                    <p>Nenhum registro</p>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                st.markdown("""
                <div class="stats-box">
                    <h4>🚀 Potencial</h4>
                    <p>Aguardando ativação</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric(
                    "🏆 Posição Geral",
                    f"#{dados_usuario['rank_performance']}" if dados_usuario['rank_performance'] > 0 else "N/A",
                    help="Posição no ranking geral de performance"
                )
            
            with col2:
                st.metric(
                    "🎥 Vídeos",
                    int(dados_usuario['total_videos']),
                    help="Total de vídeos publicados"
                )
            
            with col3:
                st.metric(
                    "👁️ Views Totais",
                    formatar_numero(dados_usuario['total_views']),
                    help="Total de visualizações"
                )
            
            with col4:
                st.metric(
                    "❤️ Curtidas",
                    formatar_numero(dados_usuario['total_likes']),
                    help="Total de curtidas recebidas"
                )
            
            with col5:
                st.metric(
                    "📈 Engajamento",
                    f"{dados_usuario['taxa_engajamento']:.1f}%",
                    help="Taxa de engajamento média"
                )
        
        st.divider()
        
        if eh_inativo:
            # Análise para usuário inativo
            st.subheader("😴 Análise de Usuário Inativo")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                <div class="warning-box">
                    <h4>⚠️ Status Atual</h4>
                    <p>Este usuário não possui nenhuma atividade registrada no sistema.</p>
                    <ul>
                        <li>0 vídeos publicados</li>
                        <li>0 visualizações</li>
                        <li>0 interações</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("""
                <div class="success-box">
                    <h4>🚀 Próximos Passos Recomendados</h4>
                    <ul>
                        <li>📱 Configurar contas nas plataformas</li>
                        <li>🎥 Publicar primeiro vídeo</li>
                        <li>📅 Estabelecer rotina de postagem</li>
                        <li>🎯 Definir nicho de conteúdo</li>
                        <li>💡 Estudar tendências da área</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            
            # Estatísticas gerais para contexto
            st.subheader("📊 Contexto Geral da Plataforma")
            usuarios_ativos = df_usuarios[df_usuarios['total_views'] > 0]
            
            if not usuarios_ativos.empty:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("📊 Média de Views", formatar_numero(usuarios_ativos['total_views'].mean()))
                with col2:
                    st.metric("🎥 Média de Vídeos", f"{usuarios_ativos['total_videos'].mean():.0f}")
                with col3:
                    st.metric("📈 Engajamento Médio", f"{usuarios_ativos['taxa_engajamento'].mean():.1f}%")
                with col4:
                    st.metric("🏆 Score Médio", f"{usuarios_ativos['score_performance'].mean():.1f}")
                
                st.info("💡 **Dica:** Estes são os números médios dos usuários ativos. Use como referência para suas primeiras metas!")
        
        else:
            # Análise detalhada para usuário ativo
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Comparação com a média
                st.subheader("📊 Comparação com Usuários Ativos")
                
                usuarios_ativos = df_usuarios[df_usuarios['total_views'] > 0]
                media_views = usuarios_ativos['total_views'].mean()
                media_likes = usuarios_ativos['total_likes'].mean()
                media_engagement = usuarios_ativos['taxa_engajamento'].mean()
                media_videos = usuarios_ativos['total_videos'].mean()
                
                comparacao_data = {
                    'Métrica': ['Views', 'Curtidas', 'Engajamento %', 'Vídeos'],
                    'Usuário': [
                        dados_usuario['total_views'],
                        dados_usuario['total_likes'],
                        dados_usuario['taxa_engajamento'],
                        dados_usuario['total_videos']
                    ],
                    'Média Geral': [media_views, media_likes, media_engagement, media_videos]
                }
                
                df_comp = pd.DataFrame(comparacao_data)
                
                fig_comp = px.bar(
                    df_comp,
                    x='Métrica',
                    y=['Usuário', 'Média Geral'],
                    title="Comparação: Usuário vs Média de Usuários Ativos",
                    barmode='group',
                    color_discrete_sequence=['#667eea', '#764ba2']
                )
                st.plotly_chart(fig_comp, use_container_width=True)
                
                # Análise de plataformas
                st.subheader("📱 Distribuição por Plataforma")
                
                plataformas = {
                    'TikTok': dados_usuario.get('tiktok_views', 0),
                    'YouTube': dados_usuario.get('youtube_views', 0),
                    'Instagram': dados_usuario.get('instagram_views', 0)
                }
                
                plataformas_ativas = {k: v for k, v in plataformas.items() if v > 0}
                
                if plataformas_ativas:
                    fig_pie = px.pie(
                        values=list(plataformas_ativas.values()),
                        names=list(plataformas_ativas.keys()),
                        title="Distribuição de Views por Plataforma",
                        color_discrete_sequence=['#ff6b6b', '#4ecdc4', '#45b7d1']
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                    
                    # Detalhes por plataforma
                    st.markdown("#### 📋 Detalhes por Plataforma")
                    for plat, views in plataformas_ativas.items():
                        porcentagem = (views / dados_usuario['total_views']) * 100
                        videos = dados_usuario.get(f'{plat.lower()}_videos', 0)
                        media_plat = (views / videos) if videos > 0 else 0
                        
                        st.markdown(f"""
                        <div class="ranking-card">
                            <h4>{plat}</h4>
                            <p><strong>Views:</strong> {formatar_numero(views)} ({porcentagem:.1f}% do total)</p>
                            <p><strong>Vídeos:</strong> {videos}</p>
                            <p><strong>Média/Vídeo:</strong> {formatar_numero(media_plat)}</p>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("📱 Dados detalhados por plataforma não disponíveis")
            
            with col2:
                # Rankings específicos
                st.subheader("🏆 Posições nos Rankings")
                
                rankings = [
                    ("👁️ Views", dados_usuario['rank_views'], len(usuarios_ativos)),
                    ("❤️ Curtidas", dados_usuario['rank_likes'], len(usuarios_ativos)),
                    ("📈 Engajamento", dados_usuario['rank_engajamento'], len(usuarios_ativos)),
                    ("🏆 Performance", dados_usuario['rank_performance'], len(usuarios_ativos))
                ]
                
                for nome, posicao, total in rankings:
                    if posicao > 0:  # Só mostrar se tem ranking
                        percentil = (1 - posicao / total) * 100
                        if percentil >= 90:
                            cor = "#ffd700"
                            nivel = "TOP 10%"
                        elif percentil >= 75:
                            cor = "#c0c0c0"
                            nivel = "TOP 25%"
                        elif percentil >= 50:
                            cor = "#cd7f32"
                            nivel = "TOP 50%"
                        else:
                            cor = "#666"
                            nivel = f"TOP {percentil:.0f}%"
                        
                        st.markdown(f"""
                        <div style="background: white; padding: 1rem; border-radius: 8px; 
                                    border-left: 4px solid {cor}; margin: 0.5rem 0;">
                            <strong>{nome}</strong><br>
                            <span style="font-size: 1.2em;">#{int(posicao)}</span> de {total}<br>
                            <small style="color: {cor}; font-weight: bold;">{nivel}</small>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Insights e recomendações
                st.subheader("💡 Insights Personalizados")
                
                insights, recomendacoes = gerar_insights_usuario(dados_usuario, df_usuarios)
                
                if insights:
                    for insight in insights:
                        st.markdown(f"""
                        <div class="insight-box">
                            <p style="margin: 0;"><strong>{insight}</strong></p>
                        </div>
                        """, unsafe_allow_html=True)
                
                if recomendacoes:
                    st.subheader("🎯 Recomendações")
                    for rec in recomendacoes:
                        st.markdown(f"""
                        <div class="warning-box">
                            <p style="margin: 0;">{rec}</p>
                        </div>
                        """, unsafe_allow_html=True)

def pagina_videos_completa(df_videos):
    """Análise completa de TODOS os vídeos"""
    st.markdown('<div class="main-header"><h1>🎬 Análise Completa de Vídeos</h1><p>Todos os Vídeos com Links e Filtros Avançados</p></div>', unsafe_allow_html=True)
    
    # Mostrar estatísticas do carregamento
    if 'total_videos_banco' in st.session_state and 'videos_carregados' in st.session_state:
        total_banco = st.session_state['total_videos_banco']
        carregados = st.session_state['videos_carregados']
        
        if carregados < total_banco:
            st.warning(f"⚠️ Carregados {carregados:,} de {total_banco:,} vídeos do banco. Alguns vídeos podem não ter usuário associado.")
        else:
            st.success(f"✅ Todos os {carregados:,} vídeos carregados com sucesso!")
    
    if df_videos.empty:
        st.error("❌ Nenhum vídeo encontrado no banco de dados")
        return
    
    # Estatísticas gerais
    total_videos = len(df_videos)
    videos_com_link = len(df_videos[df_videos['tem_link'] == True]) if 'tem_link' in df_videos.columns else 0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🎬 Total de Vídeos", f"{total_videos:,}")
    with col2:
        st.metric("🔗 Com Links", f"{videos_com_link:,}")
    with col3:
        porcentagem_links = (videos_com_link / total_videos * 100) if total_videos > 0 else 0
        st.metric("📊 % com Links", f"{porcentagem_links:.1f}%")
    with col4:
        if 'views' in df_videos.columns:
            total_views_safe = pd.to_numeric(df_videos['views'], errors='coerce').fillna(0).sum()
            st.metric("👁️ Views Totais", formatar_numero(total_views_safe))
    
    st.divider()
    
    # Filtros avançados
    st.subheader("🎯 Filtros Avançados")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        plataformas = ['Todas'] + sorted(df_videos['platform'].dropna().unique().tolist()) if 'platform' in df_videos.columns else ['Todas']
        plataforma = st.selectbox("📱 Plataforma:", plataformas)
    
    with col2:
        usuarios = ['Todos'] + sorted(df_videos['discord_username'].dropna().unique().tolist()) if 'discord_username' in df_videos.columns else ['Todos']
        usuario = st.selectbox("👤 Usuário:", usuarios)
    
    with col3:
        min_views = st.number_input("👁️ Views mínimas:", min_value=0, value=0, step=100)
    
    with col4:
        apenas_com_link = st.checkbox("🔗 Apenas com links", value=False)
    
    with col5:
        ordenacao_opcoes = {
            "📅 Mais Recentes": ("id", False),
            "👁️ Mais Views": ("views", False),
            "❤️ Mais Curtidas": ("likes", False),
            "📈 Maior Engajamento": ("engagement_rate", False),
            "🏆 Melhor Score": ("video_score", False)
        }
        ordenacao = st.selectbox("🔄 Ordenar por:", list(ordenacao_opcoes.keys()))
    
    # Aplicar filtros
    df_filtrado = df_videos.copy()
    
    if plataforma != 'Todas' and 'platform' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['platform'] == plataforma]
    
    if usuario != 'Todos' and 'discord_username' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['discord_username'] == usuario]
    
    if 'views' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['views'] >= min_views]
    
    if apenas_com_link and 'tem_link' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['tem_link'] == True]
    
    # Aplicar ordenação
    coluna_ord, ascending = ordenacao_opcoes[ordenacao]
    if coluna_ord in df_filtrado.columns:
        df_filtrado = df_filtrado.sort_values(coluna_ord, ascending=ascending)
    
    # Mostrar resultados dos filtros
    st.info(f"🔍 Filtros aplicados: {len(df_filtrado):,} vídeos de {total_videos:,} total")
    
    st.divider()
    
    # Abas principais
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Lista Paginada", "🏆 Top Vídeos", "📊 Análises", "🔍 Busca Avançada"
    ])
    
    with tab1:
        st.subheader("📋 Lista Completa de Vídeos")
        
        if df_filtrado.empty:
            st.warning("⚠️ Nenhum vídeo encontrado com os filtros aplicados")
        else:
            # Controles de paginação melhorados
            col1, col2, col3 = st.columns(3)
            
            with col1:
                videos_por_pagina = st.selectbox("Vídeos por página:", [10, 20, 50, 100], index=2)
            
            with col2:
                total_paginas = max(1, (len(df_filtrado) - 1) // videos_por_pagina + 1)
                pagina_atual = st.number_input("Página:", min_value=1, max_value=total_paginas, value=1)
            
            with col3:
                st.metric("📄 Total de Páginas", total_paginas)
            
            # Calcular range da página
            inicio = (pagina_atual - 1) * videos_por_pagina
            fim = min(inicio + videos_por_pagina, len(df_filtrado))
            df_pagina = df_filtrado.iloc[inicio:fim]
            
            st.info(f"📊 Mostrando vídeos {inicio + 1:,} a {fim:,} de {len(df_filtrado):,} filtrados")
            
            # Exibir vídeos
            for idx, (_, video) in enumerate(df_pagina.iterrows()):
                titulo = video.get('title', f'Vídeo #{video.get("id", idx+1)}')
                categoria = video.get('categoria_video', '📊 Sem categoria')
                
                with st.expander(f"{categoria} {titulo[:100]}..."):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        # Informações principais
                        st.markdown("#### 📋 Informações do Vídeo")
                        if 'discord_username' in video.index:
                            st.write(f"👤 **Criador:** {video['discord_username']}")
                        if 'platform' in video.index:
                            st.write(f"📱 **Plataforma:** {video['platform']}")
                        if 'title' in video.index:
                            st.write(f"📝 **Título:** {video['title']}")
                        
                        # Link do vídeo - DESTAQUE
                        if 'url' in video.index and pd.notna(video['url']) and video['url'] != '':
                            st.markdown(f"""
                            <div style="background: linear-gradient(135deg, #28a745, #20c997); 
                                        padding: 1.5rem; border-radius: 12px; margin: 1rem 0; text-align: center;">
                                <a href="{video['url']}" target="_blank" 
                                   style="color: white; text-decoration: none; font-weight: bold; font-size: 1.2em;">
                                    🔗 ASSISTIR VÍDEO ORIGINAL
                                </a>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown("""
                            <div style="background: #f8f9fa; padding: 1.5rem; border-radius: 12px; 
                                        border: 2px dashed #dee2e6; margin: 1rem 0; text-align: center;">
                                <span style="color: #6c757d; font-weight: bold;">🔗 Link não disponível</span>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    with col2:
                        # Métricas básicas
                        st.markdown("#### 📊 Métricas")
                        if 'views' in video.index:
                            st.metric("👁️ Views", formatar_numero(video['views']))
                        if 'likes' in video.index:
                            st.metric("❤️ Curtidas", formatar_numero(video['likes']))
                        if 'comments' in video.index:
                            st.metric("💬 Comentários", formatar_numero(video['comments']))
                    
                    with col3:
                        # Métricas avançadas
                        st.markdown("#### 🎯 Performance")
                        if 'engagement_rate' in video.index:
                            st.metric("📈 Engajamento", f"{video['engagement_rate']:.2f}%")
                        if 'video_score' in video.index:
                            st.metric("🏆 Score", f"{video['video_score']:.1f}")
                        if 'interactions' in video.index:
                            st.metric("💪 Interações", formatar_numero(video['interactions']))
            
            # Navegação da página
            if total_paginas > 1:
                st.divider()
                col1, col2, col3 = st.columns([1, 2, 1])
                
                with col1:
                    if pagina_atual > 1:
                        if st.button("⬅️ Página Anterior"):
                            st.rerun()
                
                with col2:
                    st.markdown(f"<div style='text-align: center;'><strong>Página {pagina_atual} de {total_paginas}</strong></div>", unsafe_allow_html=True)
                
                with col3:
                    if pagina_atual < total_paginas:
                        if st.button("Próxima Página ➡️"):
                            st.rerun()
    
    with tab2:
        st.subheader("🏆 Top Vídeos por Categoria")
        
        # Controle de quantidade
        top_quantidade = st.selectbox("📊 Quantidade no top:", [10, 20, 50, 100], index=1)
        
        subtabs = st.tabs(["👁️ Mais Views", "❤️ Mais Curtidas", "📈 Maior Engajamento", "🔗 Melhores com Links"])
        
        with subtabs[0]:  # Mais Views
            if 'views' in df_filtrado.columns and not df_filtrado.empty:
                top_views = df_filtrado.nlargest(top_quantidade, 'views')
                
                # Gráfico
                fig = px.bar(
                    top_views.head(20),  # Limitar gráfico a 20 para visualização
                    x='views',
                    y='title' if 'title' in top_views.columns else 'id',
                    orientation='h',
                    title=f"Top 20 Vídeos - Mais Views",
                    color='views',
                    color_continuous_scale='Blues'
                )
                fig.update_yaxes(categoryorder='total ascending')
                fig.update_layout(height=600)
                st.plotly_chart(fig, use_container_width=True)
                
                # Lista detalhada
                for i, (_, video) in enumerate(top_views.iterrows(), 1):
                    st.markdown(f"""
                    <div class="video-card">
                        <h4>#{i} - {video.get('title', 'Sem título')[:80]}...</h4>
                        <p><strong>👤 Criador:</strong> {video.get('discord_username', 'N/A')}</p>
                        <p><strong>📱 Plataforma:</strong> {video.get('platform', 'N/A')}</p>
                        <p><strong>👁️ Views:</strong> {formatar_numero(video['views'])}</p>
                        <p><strong>❤️ Curtidas:</strong> {formatar_numero(video.get('likes', 0))}</p>
                        {'<p><strong>📈 Engajamento:</strong> ' + f"{video['engagement_rate']:.2f}%" + '</p>' if 'engagement_rate' in video.index else ''}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if 'url' in video.index and pd.notna(video['url']) and video['url'] != '':
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #007bff, #0056b3); 
                                    padding: 1rem; border-radius: 8px; margin: 0.5rem 0; text-align: center;">
                            <a href="{video['url']}" target="_blank" 
                               style="color: white; text-decoration: none; font-weight: bold;">
                                🔗 ASSISTIR VÍDEO
                            </a>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.divider()
            else:
                st.info("ℹ️ Dados de views não disponíveis")
        
        with subtabs[1]:  # Mais Curtidas
            if 'likes' in df_filtrado.columns and not df_filtrado.empty:
                top_likes = df_filtrado.nlargest(top_quantidade, 'likes')
                
                for i, (_, video) in enumerate(top_likes.iterrows(), 1):
                    st.markdown(f"""
                    <div class="video-card">
                        <h4>#{i} - {video.get('title', 'Sem título')[:80]}...</h4>
                        <p><strong>👤 Criador:</strong> {video.get('discord_username', 'N/A')}</p>
                        <p><strong>❤️ Curtidas:</strong> {formatar_numero(video['likes'])}</p>
                        <p><strong>👁️ Views:</strong> {formatar_numero(video.get('views', 0))}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if 'url' in video.index and pd.notna(video['url']) and video['url'] != '':
                        st.markdown(f"🔗 **[Ver Vídeo Original]({video['url']})**")
                    
                    st.divider()
        
        with subtabs[2]:  # Maior Engajamento
            if 'engagement_rate' in df_filtrado.columns and not df_filtrado.empty:
                # Filtrar vídeos com pelo menos 100 views
                df_eng = df_filtrado[df_filtrado['views'] >= 100] if 'views' in df_filtrado.columns else df_filtrado
                top_engagement = df_eng.nlargest(top_quantidade, 'engagement_rate')
                
                for i, (_, video) in enumerate(top_engagement.iterrows(), 1):
                    st.markdown(f"""
                    <div class="video-card">
                        <h4>#{i} - {video.get('title', 'Sem título')[:80]}...</h4>
                        <p><strong>👤 Criador:</strong> {video.get('discord_username', 'N/A')}</p>
                        <p><strong>📈 Engajamento:</strong> {video['engagement_rate']:.2f}%</p>
                        <p><strong>👁️ Views:</strong> {formatar_numero(video.get('views', 0))}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if 'url' in video.index and pd.notna(video['url']) and video['url'] != '':
                        st.markdown(f"🔗 **[Ver Vídeo Original]({video['url']})**")
                    
                    st.divider()
        
        with subtabs[3]:  # Melhores com Links
            videos_com_link = df_filtrado[df_filtrado['tem_link'] == True] if 'tem_link' in df_filtrado.columns else df_filtrado[df_filtrado['url'].notna() & (df_filtrado['url'] != '')]
            
            if not videos_com_link.empty:
                # Ordenar por views para mostrar os melhores
                if 'views' in videos_com_link.columns:
                    videos_com_link = videos_com_link.sort_values('views', ascending=False)
                
                st.success(f"✅ Encontrados {len(videos_com_link):,} vídeos com links disponíveis")
                
                top_com_links = videos_com_link.head(top_quantidade)
                
                for i, (_, video) in enumerate(top_com_links.iterrows(), 1):
                    st.markdown(f"""
                    <div class="video-card">
                        <h4>#{i} - {video.get('title', 'Sem título')[:80]}...</h4>
                        <p><strong>👤 Criador:</strong> {video.get('discord_username', 'N/A')}</p>
                        <p><strong>📱 Plataforma:</strong> {video.get('platform', 'N/A')}</p>
                        <p><strong>👁️ Views:</strong> {formatar_numero(video.get('views', 0))}</p>
                        <p><strong>❤️ Curtidas:</strong> {formatar_numero(video.get('likes', 0))}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #28a745, #20c997); 
                                padding: 1.5rem; border-radius: 10px; margin: 1rem 0; text-align: center;">
                        <a href="{video['url']}" target="_blank" 
                           style="color: white; text-decoration: none; font-weight: bold; font-size: 1.1em;">
                            🔗 ASSISTIR VÍDEO AGORA
                        </a>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.divider()
            else:
                st.warning("⚠️ Nenhum vídeo com link encontrado nos filtros aplicados")
    
    with tab3:
        st.subheader("📊 Análises e Estatísticas")
        
        if df_filtrado.empty:
            st.warning("⚠️ Nenhum dado para análise")
        else:
            col1, col2 = st.columns(2)
            
            with col1:
                # Distribuição por plataforma
                if 'platform' in df_filtrado.columns:
                    dist_plat = df_filtrado['platform'].value_counts()
                    
                    fig_plat = px.pie(
                        values=dist_plat.values,
                        names=dist_plat.index,
                        title="📱 Distribuição por Plataforma"
                    )
                    st.plotly_chart(fig_plat, use_container_width=True)
            
            with col2:
                # Distribuição de engajamento
                if 'categoria_video' in df_filtrado.columns:
                    dist_cat = df_filtrado['categoria_video'].value_counts()
                    
                    fig_cat = px.bar(
                        x=dist_cat.index,
                        y=dist_cat.values,
                        title="📈 Distribuição por Categoria de Engajamento",
                        color=dist_cat.values,
                        color_continuous_scale='Viridis'
                    )
                    st.plotly_chart(fig_cat, use_container_width=True)
            
            # Estatísticas detalhadas
            st.subheader("📋 Estatísticas Detalhadas")
            
            if 'views' in df_filtrado.columns:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("📊 Total de Vídeos", f"{len(df_filtrado):,}")
                with col2:
                    st.metric("👁️ Views Totais", formatar_numero(df_filtrado['views'].sum()))
                with col3:
                    st.metric("📈 Engajamento Médio", f"{df_filtrado['engagement_rate'].mean():.2f}%" if 'engagement_rate' in df_filtrado.columns else "N/A")
                with col4:
                    st.metric("🔗 Taxa com Links", f"{(len(df_filtrado[df_filtrado['tem_link'] == True]) / len(df_filtrado) * 100):.1f}%" if 'tem_link' in df_filtrado.columns and len(df_filtrado) > 0 else "N/A")
                
                # Tabela de estatísticas
                estatisticas = {
                    'Métrica': ['Views', 'Curtidas', 'Comentários', 'Engajamento %'],
                    'Média': [
                        df_filtrado['views'].mean(),
                        df_filtrado['likes'].mean() if 'likes' in df_filtrado.columns else 0,
                        df_filtrado['comments'].mean() if 'comments' in df_filtrado.columns else 0,
                        df_filtrado['engagement_rate'].mean() if 'engagement_rate' in df_filtrado.columns else 0
                    ],
                    'Mediana': [
                        df_filtrado['views'].median(),
                        df_filtrado['likes'].median() if 'likes' in df_filtrado.columns else 0,
                        df_filtrado['comments'].median() if 'comments' in df_filtrado.columns else 0,
                        df_filtrado['engagement_rate'].median() if 'engagement_rate' in df_filtrado.columns else 0
                    ],
                    'Máximo': [
                        df_filtrado['views'].max(),
                        df_filtrado['likes'].max() if 'likes' in df_filtrado.columns else 0,
                        df_filtrado['comments'].max() if 'comments' in df_filtrado.columns else 0,
                        df_filtrado['engagement_rate'].max() if 'engagement_rate' in df_filtrado.columns else 0
                    ]
                }
                
                df_stats = pd.DataFrame(estatisticas)
                
                st.dataframe(
                    df_stats,
                    column_config={
                        "Métrica": "📊 Métrica",
                        "Média": st.column_config.NumberColumn("📈 Média", format="%.2f"),
                        "Mediana": st.column_config.NumberColumn("📊 Mediana", format="%.2f"),
                        "Máximo": st.column_config.NumberColumn("🔝 Máximo", format="%.0f")
                    },
                    hide_index=True,
                    use_container_width=True
                )
    
    with tab4:
        st.subheader("🔍 Busca Avançada")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if 'title' in df_filtrado.columns:
                termo_busca = st.text_input(
                    "🔎 Buscar no título:", 
                    placeholder="Ex: tutorial, review, gameplay, como fazer...",
                    help="Digite palavras-chave para buscar nos títulos dos vídeos"
                )
                
                if termo_busca:
                    videos_encontrados = df_filtrado[
                        df_filtrado['title'].str.contains(termo_busca, case=False, na=False)
                    ]
                    
                    if not videos_encontrados.empty:
                        st.success(f"✅ Encontrados {len(videos_encontrados):,} vídeos com '{termo_busca}'")
                        
                        # Ordenar por views
                        if 'views' in videos_encontrados.columns:
                            videos_encontrados = videos_encontrados.sort_values('views', ascending=False)
                        
                        # Limitar a 50 resultados para performance
                        videos_mostrar = videos_encontrados.head(50)
                        
                        if len(videos_encontrados) > 50:
                            st.info(f"📊 Mostrando os 50 melhores de {len(videos_encontrados)} encontrados")
                        
                        for i, (_, video) in enumerate(videos_mostrar.iterrows(), 1):
                            st.markdown(f"""
                            <div class="video-card">
                                <h4>#{i} - {video['title']}</h4>
                                <p><strong>👤 Criador:</strong> {video.get('discord_username', 'N/A')}</p>
                                <p><strong>📱 Plataforma:</strong> {video.get('platform', 'N/A')}</p>
                                <p><strong>👁️ Views:</strong> {formatar_numero(video.get('views', 0))}</p>
                                <p><strong>❤️ Curtidas:</strong> {formatar_numero(video.get('likes', 0))}</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            if 'url' in video.index and pd.notna(video['url']) and video['url'] != '':
                                st.markdown(f"""
                                <div style="background: linear-gradient(135deg, #6f42c1, #5a2d91); 
                                            padding: 1rem; border-radius: 8px; margin: 0.5rem 0; text-align: center;">
                                    <a href="{video['url']}" target="_blank" 
                                       style="color: white; text-decoration: none; font-weight: bold;">
                                        🔗 VER VÍDEO
                                    </a>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            st.divider()
                    else:
                        st.warning(f"⚠️ Nenhum vídeo encontrado com o termo '{termo_busca}'")
            else:
                st.info("ℹ️ Campo de título não disponível para busca")
        
        with col2:
            # Busca por criador
            if 'discord_username' in df_filtrado.columns:
                st.markdown("#### 👤 Busca por Criador")
                
                criadores_unicos = sorted(df_filtrado['discord_username'].dropna().unique())
                criador_busca = st.selectbox("Selecione um criador:", [''] + criadores_unicos)
                
                if criador_busca:
                    videos_criador = df_filtrado[df_filtrado['discord_username'] == criador_busca]
                    
                    if not videos_criador.empty:
                        st.success(f"✅ {len(videos_criador)} vídeos de {criador_busca}")
                        
                        # Estatísticas do criador
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("🎥 Total Vídeos", len(videos_criador))
                            if 'views' in videos_criador.columns:
                                st.metric("👁️ Views Totais", formatar_numero(videos_criador['views'].sum()))
                        with col2:
                            if 'likes' in videos_criador.columns:
                                st.metric("❤️ Curtidas Totais", formatar_numero(videos_criador['likes'].sum()))
                            if 'engagement_rate' in videos_criador.columns:
                                st.metric("📈 Engajamento Médio", f"{videos_criador['engagement_rate'].mean():.2f}%")
                        
                        # Mostrar alguns vídeos do criador
                        st.markdown("#### 🎬 Últimos Vídeos")
                        videos_recentes = videos_criador.head(10)
                        
                        for i, (_, video) in enumerate(videos_recentes.iterrows(), 1):
                            with st.expander(f"🎥 {video.get('title', f'Vídeo #{i}')}"):
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    if 'views' in video.index:
                                        st.write(f"👁️ **Views:** {formatar_numero(video['views'])}")
                                    if 'likes' in video.index:
                                        st.write(f"❤️ **Curtidas:** {formatar_numero(video['likes'])}")
                                    if 'platform' in video.index:
                                        st.write(f"📱 **Plataforma:** {video['platform']}")
                                
                                with col2:
                                    if 'engagement_rate' in video.index:
                                        st.write(f"📈 **Engajamento:** {video['engagement_rate']:.2f}%")
                                    if 'url' in video.index and pd.notna(video['url']) and video['url'] != '':
                                        st.markdown(f"🔗 **[Ver Vídeo]({video['url']})**")
                                    else:
                                        st.write("🔗 **Link:** Não disponível")

# ========== FUNÇÃO PRINCIPAL ==========
def main():
    """Função principal do dashboard completo"""
    
    # Inicializar session state
    if 'mostrar_explicacao' not in st.session_state:
        st.session_state['mostrar_explicacao'] = False
    
    # Header principal
    st.markdown("""
    <div class="main-header">
        <h1>📈 TrendX Analytics - Métricas Reais</h1>
        <p>Dashboard com Fórmulas Oficiais das Redes Sociais</p>
        <small style="opacity: 0.8;">✨ Fórmulas reais do TikTok, YouTube e Instagram • 🎬 Todos os vídeos • 🔗 Links diretos • 💡 Análises precisas</small>
    </div>
    """, unsafe_allow_html=True)
    
    # Verificar banco de dados
    if not os.path.exists(DB_PATH):
        st.error(f"❌ Banco de dados não encontrado: {DB_PATH}")
        st.info("📁 Certifique-se de que o arquivo do banco está na mesma pasta do script.")
        st.info(f"🔍 Arquivo esperado: `{DB_PATH}`")
        st.stop()
    
    # Carregar dados com indicador de progresso
    try:
        with st.spinner("🔄 Carregando TODOS os dados do banco..."):
            progress_bar = st.progress(0)
            
            # Carregar usuários
            progress_bar.progress(25)
            df_usuarios = carregar_dados_usuarios_completo()
            
            # Carregar vídeos
            progress_bar.progress(75)
            df_videos = carregar_videos_completo()
            
            progress_bar.progress(100)
            st.success("✅ Dados carregados com sucesso!")
            
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados do banco: {str(e)}")
        st.info("💡 **Possíveis soluções:**")
        st.info("1. Verifique se o arquivo do banco não está corrompido")
        st.info("2. Confirme se as tabelas 'cached_stats' e 'valid_videos' existem")
        st.info("3. Verifique se as colunas têm os tipos de dados corretos")
        st.stop()
    
    # Verificar se dados foram carregados
    if df_usuarios.empty and df_videos.empty:
        st.error("❌ Nenhum dado encontrado no banco!")
        st.info("💡 Verifique se as tabelas 'cached_stats' e 'valid_videos' existem e têm dados.")
        st.stop()
    
    # Sidebar de navegação
    st.sidebar.markdown("## 🧭 Navegação Principal")
    
    paginas = [
        "📊 Dashboard Executivo",
        "🏆 Rankings Completos", 
        "👤 Análise Individual",
        "🎬 Vídeos Completos"
    ]
    
    # Adicionar ícones e descrições
    descricoes = [
        "Visão geral de todos os usuários",
        "Rankings com controles avançados",
        "Análise detalhada por usuário",
        "Todos os vídeos com links"
    ]
    
    pagina_selecionada = st.sidebar.radio(
        "Escolha a análise:",
        paginas,
        help="Selecione a página de análise desejada"
    )
    
    # Mostrar descrição da página selecionada
    idx_pagina = paginas.index(pagina_selecionada)
    st.sidebar.info(f"📋 {descricoes[idx_pagina]}")
    
    # Status dos dados na sidebar
    st.sidebar.divider()
    st.sidebar.markdown("### 📊 Status Completo dos Dados")
    
    # Estatísticas dos usuários
    if not df_usuarios.empty:
        total_usuarios = len(df_usuarios)
        usuarios_ativos = len(df_usuarios[df_usuarios['total_views'] > 0])
        usuarios_inativos = total_usuarios - usuarios_ativos
        
        st.sidebar.metric("👥 Total Usuários", f"{total_usuarios:,}")
        st.sidebar.metric("🟢 Usuários Ativos", f"{usuarios_ativos:,}")
        st.sidebar.metric("😴 Usuários Inativos", f"{usuarios_inativos:,}")
        
        if usuarios_ativos > 0:
            taxa_ativacao = (usuarios_ativos / total_usuarios) * 100
            st.sidebar.metric("📈 Taxa de Ativação", f"{taxa_ativacao:.1f}%")
    
    # Estatísticas dos vídeos
    if not df_videos.empty:
        st.sidebar.divider()
        st.sidebar.markdown("### 🎬 Estatísticas de Vídeos")
        
        total_videos = len(df_videos)
        st.sidebar.metric("🎥 Total de Vídeos", f"{total_videos:,}")
        
        if 'tem_link' in df_videos.columns:
            videos_com_link = len(df_videos[df_videos['tem_link'] == True])
            st.sidebar.metric("🔗 Com Links", f"{videos_com_link:,}")
            
            if total_videos > 0:
                porcentagem_links = (videos_com_link / total_videos) * 100
                st.sidebar.metric("📊 % com Links", f"{porcentagem_links:.1f}%")
        
        if 'views' in df_videos.columns:
            total_views_videos = df_videos['views'].sum()
            st.sidebar.metric("👁️ Views Totais", formatar_numero(total_views_videos))
    
    # Informações do sistema
    st.sidebar.divider()
    st.sidebar.markdown("### ⚙️ Informações do Sistema")
    
    # Tamanho do banco
    if os.path.exists(DB_PATH):
        tamanho_db = os.path.getsize(DB_PATH) / (1024 * 1024)  # MB
        st.sidebar.metric("💾 Tamanho do Banco", f"{tamanho_db:.1f} MB")
    
    # Informações de carregamento
    if 'total_videos_banco' in st.session_state:
        total_banco = st.session_state['total_videos_banco']
        carregados = st.session_state.get('videos_carregados', 0)
        
        if carregados < total_banco:
            st.sidebar.warning(f"⚠️ {carregados:,}/{total_banco:,} vídeos carregados")
        else:
            st.sidebar.success(f"✅ Todos os {total_banco:,} vídeos carregados")
    
    # Controles de cache
    st.sidebar.divider()
    st.sidebar.markdown("### 🔄 Controles")
    
    if st.sidebar.button("🔄 Recarregar Dados", help="Limpa o cache e recarrega dados do banco"):
        st.cache_data.clear()
        st.rerun()
    
    # Informações sobre as funcionalidades
    st.sidebar.divider()
    st.sidebar.markdown("### ℹ️ Como Funciona")
    
    with st.sidebar.expander("📊 Fórmulas de Engajamento Reais:"):
        st.markdown("""
        **🎵 TikTok:**
        `(Curtidas + Comentários + Shares) / Views × 100`
        
        **📺 YouTube:**
        `(Curtidas + Comentários) / Views × 100`
        
        **📸 Instagram:**
        `(Curtidas + Comentários + Shares) / Views × 100`
        
        **🏆 Score de Performance:**
        - 50% Taxa de Engajamento Real
        - 30% Volume de Alcance  
        - 20% Consistência (Views/Vídeo)
        """)
    
    with st.sidebar.expander("📋 O que este dashboard oferece:"):
        st.markdown("""
        **👥 Usuários:**
        - Todos os usuários (ativos e inativos)
        - Rankings com fórmulas reais das redes
        - Análises individuais completas
        
        **🎬 Vídeos:**
        - Todos os vídeos do banco
        - Links diretos quando disponíveis
        - Engajamento calculado por plataforma
        
        **📊 Análises:**
        - Métricas oficiais de cada rede
        - Comparações precisas
        - Insights baseados em dados reais
        
        **🎯 Controles:**
        - Escolha quantos mostrar
        - Incluir/excluir inativos
        - Filtros por plataforma específica
        """)
    
    # Nova aba para explicar as métricas
    if st.sidebar.button("📖 Ver Explicação Completa das Métricas"):
        st.session_state['mostrar_explicacao'] = True
    
    # Mostrar explicação se solicitado
    if st.session_state.get('mostrar_explicacao', False):
        with st.expander("📖 Explicação Completa das Métricas", expanded=True):
            st.markdown("""
            ## 🧮 Como São Calculadas as Métricas (Fórmulas Reais)
            
            ### 📈 Taxa de Engajamento por Plataforma:
            
            **🎵 TikTok:**
            ```
            Taxa = (Curtidas + Comentários + Compartilhamentos) / Views × 100
            ```
            - TikTok valoriza **todas as interações** igualmente
            - Taxa boa: 3-9% | Excelente: 9%+
            
            **📺 YouTube:**
            ```
            Taxa = (Curtidas + Comentários) / Views × 100
            ```
            - YouTube **não conta shares** da mesma forma
            - Taxa boa: 2-5% | Excelente: 5%+
            
            **📸 Instagram:**
            ```
            Taxa = (Curtidas + Comentários + Compartilhamentos) / Views × 100
            ```
            - Similar ao TikTok, mas Instagram usa "alcance"
            - Taxa boa: 1-3% | Excelente: 3%+
            
            ### 🏆 Score de Performance (0-100):
            
            **1. Engajamento (50 pontos máx):**
            ```
            Pontos = Taxa de Engajamento × 5 (máx 50)
            ```
            - 10% engajamento = 50 pontos (máximo)
            - 5% engajamento = 25 pontos
            
            **2. Volume (30 pontos máx):**
            ```
            Pontos = log(Views + 1) × 3 (máx 30)
            ```
            - Usa logaritmo para não favorecer apenas "virais"
            - 100K views ≈ 30 pontos (máximo)
            
            **3. Consistência (20 pontos máx):**
            ```
            Pontos = (Views / Vídeos) × 0.002 (máx 20)
            ```
            - Média de 10K views/vídeo = 20 pontos
            - Recompensa quem mantém qualidade
            
            ### 🎯 Categorias Finais:
            - 🏆 **Elite (80-100):** Performance excepcional
            - 🥇 **Expert (60-79):** Muito bom
            - 🥈 **Avançado (40-59):** Bom
            - 🥉 **Intermediário (20-39):** Regular
            - 🌱 **Iniciante (1-19):** Começando
            - 😴 **Inativo (0):** Sem dados
            
            ### ✅ Por Que Estas Fórmulas São Melhores:
            1. **São as fórmulas reais** que cada rede social usa
            2. **Considera a plataforma principal** do criador
            3. **Mais justa** - pequenos criadores podem ter score alto
            4. **Focada no engajamento** - o que realmente importa
            """)
            
            if st.button("❌ Fechar Explicação"):
                st.session_state['mostrar_explicacao'] = False
    
    # Exibir página selecionada
    try:
        if pagina_selecionada == "📊 Dashboard Executivo":
            pagina_dashboard_executivo(df_usuarios)
        elif pagina_selecionada == "🏆 Rankings Completos":
            pagina_rankings_completos(df_usuarios)
        elif pagina_selecionada == "👤 Análise Individual":
            pagina_analise_usuario_avancada(df_usuarios)
        elif pagina_selecionada == "🎬 Vídeos Completos":
            pagina_videos_completa(df_videos)
            
    except TypeError as e:
        if "unsupported operand type" in str(e):
            st.error("❌ Erro de tipo de dados detectado!")
            st.warning("⚠️ Alguns dados no banco podem ter tipos incompatíveis.")
            st.info("💡 **Soluções específicas:**")
            st.info("1. Clique em 'Recarregar Dados' na sidebar")
            st.info("2. Verifique se há valores não-numéricos em colunas numéricas")
            st.info("3. Confirme se as colunas de views, likes, etc. são números")
            
            with st.expander("🔍 Detalhes técnicos"):
                st.code(str(e))
                st.markdown("**Causa provável:** Tentativa de operação matemática com dados categóricos ou texto")
        else:
            st.error(f"❌ Erro de tipo: {str(e)}")
            st.info("💡 Tente recarregar os dados ou verificar a estrutura do banco.")
            
    except Exception as e:
        st.error(f"❌ Erro inesperado: {str(e)}")
        st.info("💡 Tente recarregar os dados ou verificar a conexão com o banco.")
        
        with st.expander("🔍 Detalhes técnicos do erro"):
            st.code(str(e))
            st.markdown("**🛠️ Possíveis soluções:**")
            st.markdown("1. Clique em 'Recarregar Dados' na sidebar")
            st.markdown("2. Verifique se o banco de dados não está corrompido")
            st.markdown("3. Confirme se as tabelas necessárias existem")
            st.markdown("4. Verifique se as colunas têm os nomes e tipos corretos")
    
    # Footer informativo
    st.sidebar.divider()
    st.sidebar.markdown(f"""
    <div style="text-align: center; padding: 1rem; color: #666; font-size: 0.8em;">
        <strong>🚀 TrendX Analytics</strong><br>
        📅 {datetime.now().strftime('%d/%m/%Y às %H:%M')}<br>
        ⚡ Métricas Reais das Redes Sociais<br>
        💾 Banco: {DB_PATH}<br>
        🎯 Fórmulas Oficiais: TikTok, YouTube, Instagram
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()