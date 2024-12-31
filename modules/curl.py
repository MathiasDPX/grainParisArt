border_top = "╔" + "═" * 58 + "╗"
border_bottom = "╚" + "═" * 58 + "╝"
separator = "╠" + "═" * 58 + "╣"

def handle_curl(movies, day):    
    table = [border_top,
             "║{:^58}║".format("CinéBrest"),
             "║{:^58}║".format(day),
             separator]
    
    for film in movies:
        title_line = f"║ {film['title']:<57}║"
        table.append(title_line)
       
        for cinema, seances in film['seances'].items():
            cinema_line = f"║ ├─ {cinema:<54}║"
            table.append(cinema_line)
            
            # Split seances into groups of 6
            groups = [seances[i:i+6] for i in range(0, len(seances), 6)]
            
            for i, chunk in enumerate(groups):
                # Use └ for last group, ├ for others
                if i == len(groups) - 1:
                    seances_line = f"║ │        └─ {', '.join(chunk):<45}║"
                else:
                    seances_line = f"║ │        ├─ {', '.join(chunk):<45}║"
                table.append(seances_line)
       
        table.append(separator)
   
    table[-1] = border_bottom
    return "\n".join(table)+"\n"