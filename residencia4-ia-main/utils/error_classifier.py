import json
from datetime import datetime
import pytz
from typing import Optional
import os

LIMIT_C = 4.0  
LIMIT_B = 9.0  
LIMIT_A = 59.0 

def get_current_program(
    target_datetime: Optional[datetime] = None,
    schedule_file_path: str = "../utils/programacao_globo_2025.json" 
) -> str:
    """
    Determina qual programa está no ar (ou esteve no ar) com base num ficheiro de agendamento.
    ...
    """
    if not os.path.isabs(schedule_file_path):
        full_path = os.path.abspath(os.path.join(os.path.dirname(__file__), schedule_file_path))
    else:
        full_path = schedule_file_path

    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            schedule_data = json.load(f)
    except FileNotFoundError:
        return "Programação não encontrada" 
    except json.JSONDecodeError:
        return "Erro ao ler o arquivo de programação"

    tz = pytz.timezone('America/Sao_Paulo')
    
    if target_datetime is None:
        target_time = datetime.now(tz)
    else:
        if target_datetime.tzinfo is None:
            target_time = tz.localize(target_datetime)
        else:
            target_time = target_datetime.astimezone(tz)

    days_of_week = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]
    current_day = days_of_week[target_time.weekday()]

    current_hour_str = target_time.strftime("%H:%M")

    if current_day in schedule_data:
        daily_schedule = schedule_data[current_day]
        for i in range(len(daily_schedule)):
            program_start_time = daily_schedule[i]["time"]
            
            next_program_start_time = daily_schedule[i+1]["time"] if i + 1 < len(daily_schedule) else "23:59"

            if program_start_time <= current_hour_str < next_program_start_time:
                return daily_schedule[i]["program"]
                
    return "Programação Indefinida"

def classify_error(error_type: str, duration: float) -> str:
    """
    Classifica o nível de um erro (A, B, C, X) com base na sua duração em segundos.
    """
    if duration <= LIMIT_C:
        return "C"  
    elif duration <= LIMIT_B:
        return "B"  
    elif duration <= LIMIT_A:
        return "A"
    else:
        return "X"