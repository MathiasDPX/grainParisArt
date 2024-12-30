border_top = "╔" + "═" * 58 + "╗"
border_bottom = "╚" + "═" * 58 + "╝"
separator = "╠" + "═" * 58 + "╣"

def handle_curl(movies):    
    table = [border_top, "║{:^58}║".format("CinéBrest"), separator]
    
    for film in movies:
        title_line = f"║ {film['title']:<57}║"
        table.append(title_line)
        
        for cinema, seances in film['seances'].items():
            cinema_line = f"║ ├─ {cinema:<54}║"
            seances_line = f"║ │        └─ : {', '.join(seances):<43}║"
            table.extend([cinema_line, seances_line])
        
        table.append(separator)
    
    table[-1] = border_bottom
    return "\n".join(table)