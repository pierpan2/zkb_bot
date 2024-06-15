import re
from datetime import datetime
import sqlite3
import plotly.graph_objects as go
import pandas as pd
from plotting import *
from PIL import Image

def log2db(lines):
    language = "en"
    dmg_to = "to"
    dmg_from = "from"
    rep_to = "to"
    rep_by = "by"
    # Define the pattern for the combat lines
    combat_pattern = re.compile(
        r"\[ ([\d\.\s:]+) \]\s+\(combat\)\s+(\d+)\s+(from|to)\s+(.+?)\s+-\s+(.+?)\s+-\s+(.+)"
    )
    repair_pattern = re.compile(
        r"\[ ([\d\.\s:]+) \]\s+\(combat\)\s+(\d+)\s+(remote armor repaired|remote shield boosted)\s+(to|by)\s+(.+?)\s+-\s+(.+)"
    )
    # [ 2024.05.13 03:53:04 ] (combat) Your group of 250mm Railgun II misses Funny RUA completely - 250mm Railgun II
    you_miss_pattern = re.compile(
        r"\[ ([\d\.\s:]+) \] \(combat\) Your group of (.+?) misses (.+?) completely - \2"
    )
    miss_you_pattern = re.compile(
        r"\[ ([\d\.\s:]+) \] \(combat\) (.+?) misses you completely - (.+)"
    )
    # [ 2024.05.15 22:54:46 ] (combat) Warp disruption attempt from  Claw │  [NERV] to you!
    point_pattern = re.compile(
        r"\[ ([\d\.\s:]+) \] \(combat\) Warp (disruption|scramble) attempt from (.+?) to (.+)"
    )

    name = ""
    if "游戏记录" in lines[1]:
        language = "zh"
        dmg_to = "对"
        dmg_from = "来自"
        rep_to = "至"
        rep_by = "由"
        combat_pattern = re.compile(
            r"\[ ([\d\.\s:]+) \]\s+\(combat\)\s+(\d+)\s+(来自|对)\s+(.+?)\s+-\s+(.+?)\s+-\s+(.+)"
        )
        repair_pattern = re.compile(
            r"\[ ([\d\.\s:]+) \]\s+\(combat\)\s+(\d+)\s*(远程装甲维修量|远程护盾回充增量)\s*(至|由)\s*(.+?)\s+-\s+(.+)"
        )
        # 你的一组250mm Railgun II*完全没有打中DarKdeZ Ever - 250mm Railgun II*
        you_miss_pattern = re.compile(
            r"\[ ([\d\.\s:]+) \] \(combat\) 你的一组(.+?)完全没有打中(.+?) - \2"
        )
        miss_you_pattern = re.compile(
            r"\[ ([\d\.\s:]+) \] \(combat\) (.+?)完全没有打中你 - (.+)"
        )
        point_pattern = re.compile(
            r"\[ ([\d\.\s:]+) \] \(combat\) (.+?)\s*试图跃迁(扰频|扰断)\s(.+)"
        )

        # Extract the name of the listener from the second line of the file
        name = re.search(r"收听者: (.+)", lines[2]).group(1)
        print(f"战犯: {name}")
    else:
        # Extract the name of the listener from the second line of the file
        name = re.search(r"Listener: (.+)", lines[2]).group(1)
        print(f"Zhanfan: {name}")
    name = name.replace(' ', '_')
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    create_table_query = f'''
    CREATE TABLE IF NOT EXISTS {name} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT,
        time TIMESTAMP,
        number INTEGER,
        module TEXT,
        source TEXT,
        target TEXT,
        notes TEXT
    );'''
    cursor.execute(create_table_query)
    insert_query = f'''
    INSERT INTO {name} (type, time, number, module, source, target, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?);
    '''
    # for line in lines:
    for i in range(len(lines) - 1):
        line = lines[i]
        while i < len(lines) - 1 and not lines[i + 1].startswith("[ "):
            line = line.strip() + lines[i + 1]
            i += 1
        if "197-variant" in line:
            continue
        # Remove HTML tags
        clean_line = re.sub("<[^<]+?>", "", line.strip())
        # Match the cleaned line against the combat pattern
        match_damage = combat_pattern.match(clean_line)
        if match_damage:
            time_stamp = match_damage.group(1)
            dmg_number = match_damage.group(2)
            direction = match_damage.group(3)
            game_id = match_damage.group(4).strip()
            weapon = match_damage.group(5).strip()
            hit_efficiency = match_damage.group(6).strip()
            source = name if direction == dmg_to else game_id
            target = name if direction == dmg_from else game_id
            cursor.execute(insert_query, (
                'damage',
                datetime.strptime(time_stamp, '%Y.%m.%d %H:%M:%S'),
                dmg_number,
                weapon,
                source,
                target,
                hit_efficiency
            ))
            continue
        # Match the cleaned line against the repair pattern
        match_repair = repair_pattern.match(clean_line)
        # print(match)
        if match_repair:
            # print(clean_line)
            time_stamp = match_repair.group(1)
            rep_number = match_repair.group(2)
            rep_type = match_repair.group(3)
            direction = match_repair.group(4)
            game_id = match_repair.group(5).strip()
            module = match_repair.group(6).strip()
            source = name if direction == rep_to else game_id
            target = name if direction == rep_by else game_id
            cursor.execute(insert_query, (
                'repair',
                datetime.strptime(time_stamp, '%Y.%m.%d %H:%M:%S'),
                rep_number,
                module,
                source,
                target,
                rep_type
            ))
            continue
        # Match the cleaned line against the you miss pattern
        match_you_miss = you_miss_pattern.match(clean_line)
        if match_you_miss:
            time_stamp = match_you_miss.group(1)
            weapon = match_you_miss.group(2)
            game_id = match_you_miss.group(3)
            cursor.execute(insert_query, (
                'damage',
                datetime.strptime(time_stamp, '%Y.%m.%d %H:%M:%S'),
                0,
                weapon,
                name,
                game_id,
                'Misses'
            ))
            continue
        # Match the cleaned line against the miss you pattern
        match_miss_you = miss_you_pattern.match(clean_line)
        if match_miss_you:
            time_stamp = match_miss_you.group(1)
            game_id = match_miss_you.group(2)
            weapon = match_miss_you.group(3)
            cursor.execute(insert_query, (
                'damage',
                datetime.strptime(time_stamp, '%Y.%m.%d %H:%M:%S'),
                0,
                weapon,
                game_id,
                name,
                'Misses'
            ))
            continue
        # Match the cleaned line against tackle
        match_point = point_pattern.match(clean_line)
        if match_point:
            # print(match_point)
            time_stamp = match_point.group(1)
            point_type = match_point.group(2)
            point_from = match_point.group(3)
            point_to = match_point.group(4)
            if language == "zh":
                time_stamp = match_point.group(1)
                point_type = match_point.group(3)
                point_from = match_point.group(2)
                point_to = match_point.group(4)

            if point_to.endswith("!") or point_to.endswith("！"):
                point_to = point_to[:-1]
            point_type = point_type.replace('扰频', 'scramble').replace('扰断', 'disruption')
            source = name if point_from in ['你', 'you'] else point_from
            target = name if point_to in ['你', 'you'] else point_to
            cursor.execute(insert_query, (
                'tackle',
                datetime.strptime(
                    time_stamp, '%Y.%m.%d %H:%M:%S'),
                0,
                point_type,
                source,
                target,
                point_type
            ))
    conn.commit()
    return language, name, conn, cursor


def overview(name, cursor, language):
    # Query to find the total repair done
    query = f'''
        SELECT SUM(number) as total_damage
        FROM {name}
        WHERE type='repair' AND source=?
        '''
    cursor.execute(query, (name,))
    total_rep = cursor.fetchone()[0]
    total_rep = total_rep if total_rep else 0
    # use total repair = 1000 as logi threshold
    if total_rep > 1000:
        fig_rep_to_others = plot_rep_to_others(name, cursor, total_rep, language)
        # fig_rep_to_others.show()
        fig_hit_efficiency = None
    else:
        fig_hit_efficiency = plot_hit_efficiency(name, cursor, language)
        # fig_hit_efficiency.show()
        fig_rep_to_others = None
    fig_rep_dmg_receive = plot_rep_dmg_receive(name, cursor, language)
    # fig_rep_dmg_receive.show()
    fig_damage_list = plot_damage_list(name, cursor, language)
    # fig_damage_list.show()
    fig_comb_img = combine_figures([fig_rep_to_others, 
                                fig_hit_efficiency, 
                                fig_rep_dmg_receive, 
                                fig_damage_list])
    # fig_comb_img.show()
    # fig_comb_img.save('zhanfan.png')
    return fig_comb_img, fig_rep_dmg_receive

# TODO: rewrite
def plot_game_log(time_plot_stats, name=''):
    
    # Parsing the filtered data
    damages_to = []
    damages_from = []
    repairs_to = []
    repairs_from = []

    #for log in filtered_logs:
    #    if log["type"] == "damage":
    #        if log["direction"] == "to":
    #            if log['weapon'] == main_name:
    #                log['message'] = f"{log['damage_number']}, {log['hit_efficiency']} <b>To</b> {log['game_id']}, {log['weapon']}"
    #                damages_to.append(log)
    #        else:
    #            log['message'] = f"{log['damage_number']}, {log['hit_efficiency']} <b>From</b> {log['game_id']}, {log['weapon']}"
    #            damages_from.append(log)
    #    elif log["type"] == "repair":
    #        if log["direction"] == "to":
    #            log['message'] = f"{log['rep_number']} <b>To</b> {log['game_id']}, {log['module']}"
    #            repairs_to.append(log)
    #        else:
    #            log['message'] = f"{log['rep_number']} <b>From</b> {log['game_id']}, {log['module']}"
    #            repairs_from.append(log)

    # Create dataframes for each category
    df_damages_to = pd.DataFrame(damages_to)
    df_damages_from = pd.DataFrame(damages_from)
    df_repairs_to = pd.DataFrame(repairs_to)
    df_repairs_from = pd.DataFrame(repairs_from)

    # Add a 'y_value' column to handle negative values for "from" direction
    if not df_damages_to.empty:
        df_damages_to['y_value'] = df_damages_to['damage_number']
        df_damages_to['type'] = 'Damage Applied'
        df_damages_to['time_s'] = df_damages_to['time'].apply(
            lambda x: datetime.strptime(x.strip(), "%Y.%m.%d %H:%M:%S"))
    if not df_damages_from.empty:
        df_damages_from['y_value'] = df_damages_from['damage_number']
        df_damages_from['type'] = 'Damage Received'
        df_damages_from['time_s'] = df_damages_from['time'].apply(
            lambda x: datetime.strptime(x.strip(), "%Y.%m.%d %H:%M:%S"))
    if not df_repairs_to.empty:
        df_repairs_to['y_value'] = df_repairs_to['rep_number']
        df_repairs_to['type'] = 'Repair Applied'
        df_repairs_to['time_s'] = df_repairs_to['time'].apply(
            lambda x: datetime.strptime(x.strip(), "%Y.%m.%d %H:%M:%S"))
    if not df_repairs_from.empty:
        df_repairs_from['y_value'] = df_repairs_from['rep_number']
        df_repairs_from['type'] = 'Repair Received'
        df_repairs_from['time_s'] = df_repairs_from['time'].apply(
            lambda x: datetime.strptime(x.strip(), "%Y.%m.%d %H:%M:%S"))

    def aggregate_by_time(df):
        if 'weapon' in df:
            return df.groupby('time_s').agg({
                'y_value': 'sum',
                'game_id': 'first',
                'weapon': 'first',
                'damage_number': 'first',
                'hit_efficiency': 'first',
                'time': 'first',
                'message': lambda x: '<br>'.join(x),
            }).reset_index()
        if 'module' in df:
            return df.groupby('time_s').agg({
                'y_value': 'sum',
                'game_id': 'first',
                'module': 'first',
                'rep_number': 'first',
                'time': 'first',
                'message': lambda x: '<br>'.join(x),
            }).reset_index()
        return df
    # Aggregate data
    if not df_damages_to.empty:
        df_damages_to = aggregate_by_time(df_damages_to)
        df_damages_to['type'] = 'Damage Applied'
    if not df_damages_from.empty:
        df_damages_from = aggregate_by_time(df_damages_from)
        df_damages_from['type'] = 'Damage Received'
    if not df_repairs_to.empty:
        df_repairs_to = aggregate_by_time(df_repairs_to)
        df_repairs_to['type'] = 'Repair Applied'
    df_repairs_from_list = []
    if not df_repairs_from.empty:
        df_repairs_from_list = [group.reset_index(
            drop=True) for _, group in df_repairs_from.groupby('game_id')]
        i = 0
        for i in range(0, len(df_repairs_from_list)):
            df_repairs_from_list[i] = aggregate_by_time(
                df_repairs_from_list[i])
            df_repairs_from_list[i]['type'] = 'Repair Received'

    layout = dict(
        hoversubplots="axis",
        title=f'Game Damages and Repairs Log<br>Zhanfan: {name}',
        hovermode="x",
        grid=dict(rows=2, columns=1),
    )
    # Plot using Plotly Graph Objects
    fig = go.Figure(layout=layout)

    if not df_damages_to.empty:
        fig.add_trace(go.Scatter(
            x=df_damages_to['time_s'],
            y=df_damages_to['y_value'],
            xaxis="x",
            yaxis="y",
            mode='lines+markers',
            name='Damage Applied',
            line=dict(color='red'),
            customdata=df_damages_to[['message']],
            hovertemplate="%{customdata[0]}"
        ))

    if not df_damages_from.empty:
        fig.add_trace(go.Scatter(
            x=df_damages_from['time_s'],
            y=df_damages_from['y_value'],
            xaxis="x",
            yaxis="y2",
            mode='lines+markers',
            name='Damage Received',
            line=dict(color='darkred'),
            customdata=df_damages_from[['message']],
            hovertemplate="%{customdata[0]}"
        ))

    if not df_repairs_to.empty:
        fig.add_trace(go.Scatter(
            x=df_repairs_to['time_s'],
            y=df_repairs_to['y_value'],
            xaxis="x",
            yaxis="y",
            mode='lines+markers',
            name='Repair Applied',
            line=dict(color='blue'),
            customdata=df_repairs_to[['message']],
            hovertemplate="%{customdata[0]}"
        ))
    for df_r_f in df_repairs_from_list:
        if not df_r_f.empty:
            fig.add_trace(go.Scatter(
                x=df_r_f['time_s'],
                y=df_r_f['y_value'],
                xaxis="x",
                yaxis="y2",
                mode='lines+markers',
                name=f'Repair Received from {df_r_f["game_id"][0]}',
                # line=dict(color='game_id'),
                customdata=df_r_f[['message']],
                hovertemplate="%{customdata[0]}"
            ))

    # fig.show()
    # fig.write_html("plot.html")
    return fig


def all_in_one(lines):
    language, name, conn, cursor = log2db(lines)
    zhanfan_img, fig = overview(name, cursor, language)
    return zhanfan_img, fig

if __name__ == "__main__":
    # Example usage (assuming the logs are saved locally)
    file_path = "your_log_file.txt"
    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()
        language, name, conn, cursor = log2db(lines)
        zhanfan_img = overview(name, cursor, language)
        zhanfan_img.show()
        # Close the connection
        conn.close()
