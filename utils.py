import plotly.graph_objects as go
import plotly.io as pio

def generate_filtered_graph(filtered_data, name):
    # Créer le graphique avec Plotly
    fig = go.Figure()

    if 'value' in filtered_data.columns:
        fig.add_trace(go.Scatter(
            x=filtered_data['date'][(filtered_data['value'].notna()) & (filtered_data['value'] != 0)],
            y=filtered_data['value'][(filtered_data['value'].notna()) & (filtered_data['value'] != 0)],
            mode='markers',
            marker=dict(symbol='cross', color='blue'),
            name='Concentration en ng/L'
        ))

    # Tracer les points pour les valeurs du seuil de détection
    if 'less_than' in filtered_data.columns:
        fig.add_trace(go.Scatter(
            x=filtered_data['date'][filtered_data['less_than'].notna()],
            y=filtered_data['less_than'][filtered_data['less_than'].notna()],
            mode='markers',
            marker=dict(symbol='cross', color='green'),
            name='Seuil de détection'
        ))

    fig.add_hline(y=4, line=dict(color='red', dash='dash'), name='Seuil maximal pour la santé')

    fig.update_layout(
        title=f"Évolution des PFAS dans le temps ({name})",
        xaxis_title='Date',
        yaxis_title='Valeur par ng/L',
        legend_title='Légende',
        xaxis=dict(tickangle=45),
        template='plotly_white'
    )

    # Générer le HTML du graphique
    plot_html = pio.to_html(fig, full_html=False)
    return plot_html
