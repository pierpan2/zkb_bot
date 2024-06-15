import plotly.graph_objects as go
from io import BytesIO
from PIL import Image, ImageDraw
import matplotlib.pyplot as plt
import matplotlib as mpl

import matplotlib.font_manager as fm
font_name = "WenQuanYi Zen Hei"
font_path = './wryh.ttf'
prop = fm.FontProperties(fname=font_path)

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
            # fm.fontManager.addfont(font_path)
            mpl.rcParams['font.family'] = font_name
            mpl.rcParams['font.sans-serif'] = [font_name]
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
            font=dict(
                size=18,
                family=font_name
            ),
            template="plotly_white",
            annotations=[
                {
                    'text': f"{main_weapon_module[:30]}   Total Damage: {total_damage:,}   Accuracy(≥Hit): {sum(values[3:]):.2f}%",
                    'x': 0.5,
                    'y': 1.05,
                    'xref': 'paper',
                    'yref': 'paper',
                    'showarrow': False,
                    'font': {'size': 18}
                }
            ],
            height=700
        )

        # Show the plot
        # fig.show()
        return fig
    else:
        return None

def plot_rep_to_others(name, cursor, total_rep, language):
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
    categories = [target[:30] for target, number in result]
    values = [number for target, number in result]
    # Create a bar plot using Plotly
    fig = go.Figure(
        [go.Bar(x=categories, y=values, text=values, textposition='outside', marker_color='blue', textfont_size=15)])
    if language == 'zh':
        # fm.fontManager.addfont(font_path)
        mpl.rcParams['font.family'] = font_name
        mpl.rcParams['font.sans-serif'] = [font_name]
    # Customize the layout
    fig.update_layout(
        title={
            'text': f"Zhanfan: {name.replace('_', ' ')}",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        xaxis=dict(
            tickangle=30,        
            tickfont=dict(
                size=15
            )
        ),
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
        ],
        height=700
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
    # categories_dmg = [name[:30] for name, number in dmg_receive[:6] if len(name)<30]
    categories_dmg=[]
    for target, number in dmg_receive[:6]:
        if len(target) < 30:
            categories_dmg.append(target)
        else:
            categories_dmg.append(target[:18]+'...'+target[-9:])
    values_dmg = [number for target, number in dmg_receive[:6]]
    if (not rep_receive) and (not dmg_receive):
        return None
    # Create a bar plot using Plotly
    if language == 'zh':
        
        # fm.fontManager.addfont(font_path)
        mpl.rcParams['font.family'] = font_name
        mpl.rcParams['font.sans-serif'] = [font_name]
    fig = go.Figure(
        data=[
            go.Bar(x=categories_rep, y=values_rep, text=values_rep, name='Repair',
                   textposition='outside', marker_color='blue', textfont_size=15),
            go.Bar(x=categories_dmg, y=values_dmg, text=values_dmg, name='Damage', 
                   textposition='outside', marker_color='red', textfont_size=15)
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
        xaxis=dict(
            tickangle=30,        
            tickfont=dict(
                size=15
            )
        ),
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
        showlegend=True,
        height=700
    )
    # Show the plot
    # fig.show()
    return fig

def plot_damage_list(name, cursor, language):
    # Query to count the total repair from player_name to each different target
    damage_query = f'''
    SELECT target, SUM(number) as total_damage
    FROM {name}
    WHERE type='damage' AND source=?
    GROUP BY target
    ORDER BY total_damage DESC;
    '''
    cursor.execute(damage_query, (name,))
    damage_totals = cursor.fetchall()
    if not damage_totals:
        return None
    damages = [damage for target, damage in damage_totals]
    targets = [target[:30] for target, damage in damage_totals]
    fig = go.Figure(data=[go.Table(
        columnwidth=[1, 2], 
        header=dict(values=['Total Damage', 'Target'], font_size=18),
        cells=dict(values=[damages, targets], font_size=16, height=30)
    )])
    if language == 'zh':
        # fm.fontManager.addfont(font_path)
        mpl.rcParams['font.family'] = font_name
        mpl.rcParams['font.sans-serif'] = [font_name]
    fig.update_layout(
        title='Damage Summary',
        title_font_size=20,
        title_x=0.5  # Centers the title
    )
    # fig.show()
    return fig

def combine_figures(fig_list, line_thickness=3):
    fig_list = [fig for fig in fig_list if fig is not None]
    images = []
    buffers = []
    for fig in fig_list:
        img_buffer = BytesIO()
        fig.write_image(img_buffer, format='png')
        img_buffer.seek(0)
        images.append(Image.open(img_buffer))
        buffers.append(img_buffer)
    widths, heights = zip(*(i.size for i in images))
    total_height = sum(heights) + line_thickness * len(images)
    max_width = max(widths)
    combined_image = Image.new('RGB', (max_width, total_height))
    y_offset = 0
    for img in images:
        combined_image.paste(img, (0, y_offset))
        y_offset += img.height
        draw = ImageDraw.Draw(combined_image)
        draw.rectangle([0, y_offset, max_width, y_offset + line_thickness], fill='black')
        y_offset += line_thickness
    for buffer in buffers:
        buffer.close()
    return combined_image