import plotly.graph_objects as go

def plot_hit_efficiency(name, cursor, language):
    # Query to find the weapon (module) that did the most damage
    query = f'''
        SELECT module, SUM(number) as total_damage
        FROM {name}
        WHERE type='damage' AND source=?
        GROUP BY module
        ORDER BY total_damage DESC
        LIMIT 1;
        '''
    cursor.execute(query, (name,))
    # (main weapon name, total damage)
    main_weapon = cursor.fetchone()
    if main_weapon:
        main_weapon_module = main_weapon[0]
        total_damage = main_weapon[1]

        # Query to get the efficiency distribution for the main weapon
        efficiency_query = f'''
            SELECT notes, COUNT(*) as count
            FROM {name}
            WHERE type='damage' AND source=? AND module=?
            GROUP BY notes;
            '''
        cursor.execute(efficiency_query, (name, main_weapon_module))
        efficiency_distribution = cursor.fetchall()
        total_counts = sum(count for _, count in efficiency_distribution)
        efficiency_percentages = {
            eff: (count / total_counts) * 100 for eff, count in efficiency_distribution}
        categories = ["Misses", "Grazes", "Glances Off",
                      "Hits", "Penetrates", "Smashes", "Wrecks"]
        if language == "zh":
            categories = ["Misses", "轻轻擦过", "擦过", "命中", "穿透", "强力一击", "致命一击"]
        values = [efficiency_percentages.get(eff, 0) for eff in categories]

        # Create a bar plot using Plotly
        fig = go.Figure(
            [go.Bar(x=categories, y=values, text=[f'{value:.2f}%' for value in values], textposition='outside', marker_color='red', textfont_size=18)])

        # Customize the layout
        fig.update_layout(
            title={
                'text': f"Zhanfan: {name.replace('_', ' ')}",
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            xaxis_title="Efficiency",
            yaxis_title="Percentage (%)",
            yaxis=dict(tickformat=".2f"),
            font=dict(size=18),
            template="plotly_white",
            annotations=[
                {
                    'text': f"{main_weapon_module} Total Damage: {total_damage:,}",
                    'x': 0.5,
                    'y': 1.05,
                    'xref': 'paper',
                    'yref': 'paper',
                    'showarrow': False,
                    'font': {'size': 18}
                }
            ]
        )

        # Show the plot
        # fig.show()
        return fig
    else:
        return None

def plot_rep_to_others(name, cursor, total_rep):
    # Query to get the total repair done to each different target by the player
    query = f'''
        SELECT target, SUM(number) as total_repair
        FROM {name}
        WHERE type = 'repair' AND source = ?
        GROUP BY target
        ORDER BY total_repair DESC;
        '''
    # Execute the query
    cursor.execute(query, (name,))
    result = cursor.fetchall()
    categories = [name[:30] for name, number in result]
    values = [number for name, number in result]
    # Create a bar plot using Plotly
    fig = go.Figure(
        [go.Bar(x=categories, y=values, text=values, textposition='outside', marker_color='blue', textfont_size=18)])
    # Customize the layout
    fig.update_layout(
        title={
            'text': f"Zhanfan: {name.replace('_', ' ')}",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        xaxis_title="Teammates",
        yaxis_title="Repair Done",
        font=dict(size=18),
        template="plotly_white",
        annotations=[
            {
                'text': f"Total Repair: {total_rep:,}",
                'x': 0.5,
                'y': 1.05,
                'xref': 'paper',
                'yref': 'paper',
                'showarrow': False,
                'font': {'size': 18}
            }
        ]
    )
    # Show the plot
    # fig.show()
    return fig

def plot_rep_dmg_receive(name, cursor, language):
    # Query to get the total repair or damage receive
    rep_query = f'''
        SELECT source, SUM(number) as total_repair
        FROM {name}
        WHERE type = 'repair' AND target = ?
        GROUP BY source
        ORDER BY total_repair DESC;
        '''
    # Execute the repair receive query
    cursor.execute(rep_query, (name,))
    rep_receive = cursor.fetchall()
    categories_rep = [name[:30] for name, number in rep_receive]
    values_rep = [number for name, number in rep_receive]

    dmg_query = f'''
        SELECT source, SUM(number) as total_damage
        FROM {name}
        WHERE type = 'damage' AND target = ?
        GROUP BY source
        ORDER BY total_damage DESC;
        '''
    # Execute the repair receive query
    cursor.execute(dmg_query, (name,))
    dmg_receive = cursor.fetchall()
    categories_dmg = [name[:30] for name, number in dmg_receive[:6]]
    values_dmg = [number for name, number in dmg_receive[:6]]
    if (not rep_receive) and (not dmg_receive):
        return None
    # Create a bar plot using Plotly
    fig = go.Figure(
        data=[
            go.Bar(x=categories_rep, y=values_rep, text=values_rep, name='Repair',
                   textposition='outside', marker_color='blue', textfont_size=18),
            go.Bar(x=categories_dmg, y=values_dmg, text=values_dmg, name='Damage', 
                   textposition='outside', marker_color='red', textfont_size=18)
            ])
    # Customize the layout
    fig.update_layout(
        title={
            'text': f"Zhanfan: {name.replace('_', ' ')}",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        xaxis_title="Source",
        yaxis_title="Rep or Dmg Value",
        font=dict(size=18),
        template="plotly_white",
        annotations=[
            {
                'text': f"Total Repair or Damage receive",
                'x': 0.5,
                'y': 1.05,
                'xref': 'paper',
                'yref': 'paper',
                'showarrow': False,
                'font': {'size': 18}
            }
        ],
        showlegend=True
    )
    # Show the plot
    # fig.show()
    return fig
