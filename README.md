# 📈 TrendX Analytics Dashboard

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
