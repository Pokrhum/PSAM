import plotly.graph_objects as go
import plotly.io as pio
import numpy as np
import pandas as pd

def generate_filtered_graph(main_data, name):

    # Création du nouveau DataFrame en groupant par la colonne 'date'
    filtered_data = main_data.groupby('date').agg(
        value=('value', 'sum'),
        unit=('unit', 'first'),
        less_than=('less_than', 'max'),
        source_text=('source_text', 'first')
    ).reset_index()

    # Remplacer les 0 par NaN dans 'value' et remplir NaN dans 'less_than' si 'value' n'est pas NaN
    filtered_data['value'] = filtered_data['value'].apply(lambda x: np.nan if x == 0 else x)
    filtered_data.loc[filtered_data['value'].notna(), 'less_than'] = np.nan

    # Construire date_info en remplissant les NaN par une valeur par défaut
    date_info = {
        date: "<br>".join(
            [
                f"{row['substance']}: {row['value']} ng/L" if not pd.isna(row['value'])
                else f"{row['substance']}: inférieur à {row['less_than']} ng/L"
                for _, row in main_data[main_data['date'] == date].iterrows()
            ]
        ) if date in main_data['date'].unique() else "Aucune donnée"
        for date in filtered_data['date']
    }

    # Créer le graphique avec Plotly
    fig = go.Figure()

    # Tracer les points avec 'value' non-NaN
    if 'value' in filtered_data.columns:
        fig.add_trace(go.Scatter(
            x=filtered_data['date'][filtered_data['value'].notna()],
            y=filtered_data['value'][filtered_data['value'].notna()],
            mode='markers',
            marker=dict(symbol='cross', color='blue'),
            name='Concentration en ng/L',
            customdata=[date_info[date] for date in filtered_data['date'][filtered_data['value'].notna()]],
            hovertemplate=
                '<b>Date</b>: %{x}<br>' +
                '<b>Valeur</b>: %{y} ng/L<br>' +
                '<b>Répartition des PFAS</b>:<br>' +
                '%{customdata}<br>' +
                '<extra></extra>'
        ))

    # Tracer les points pour les valeurs du seuil de détection
    if 'less_than' in filtered_data.columns:
        fig.add_trace(go.Scatter(
            x=filtered_data['date'][filtered_data['less_than'].notna()],
            y=filtered_data['less_than'][filtered_data['less_than'].notna()],
            mode='markers',
            marker=dict(symbol='cross', color='green'),
            name='Seuil de détection',
            hovertemplate=(
                '<b>Date</b>: %{x}<br>' +
                '<b>Seuil de détection</b>: %{y} ng/L<br>' +
                '<extra></extra>'
            )
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
    return plot_html, filtered_data

