import pandas as pd
import os
import hashlib
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from dashboard.models import Paciente, Procedimento, Atendimento

class Command(BaseCommand):
    help = 'Importação com DEBUG para descobrir erro nos atendimentos'

    def handle(self, *args, **kwargs):
        arquivo = os.path.join(settings.BASE_DIR, 'dados_caps.xls')
        self.stdout.write(self.style.WARNING(f'Lendo arquivo: {arquivo}'))

        try:
            df = pd.read_excel(arquivo, engine='openpyxl')
        except Exception:
            self.stdout.write(self.style.ERROR('Erro ao ler arquivo.'))
            return

        df.columns = df.columns.str.strip().str.upper()
        self.stdout.write('Iniciando... Se houver erro, ele aparecerá abaixo:')
        
        # Tenta achar a coluna de motivo
        col_motivo = 'CO_MOTIVO_SAIDA_PERMANENCIA'
        if col_motivo not in df.columns:
            for col in df.columns:
                if 'MOTIVO' in col and 'SAIDA' in col: col_motivo = col; break

        count_erros = 0

        for index, row in df.iterrows():
            try:
                # --- 1. PACIENTE (Isso está funcionando) ---
                nome = str(row.get('NM_PACIENTE', 'Desconhecido')).strip().upper()
                if nome == '' or nome == 'NAN': continue

                cpf_limpo = ''.join(filter(str.isdigit, str(row.get('CO_CPF_PACIENTE', ''))))
                cns_limpo = ''.join(filter(str.isdigit, str(row.get('CO_CNS_PACIENTE', ''))))
                
                identificador = cpf_limpo if (len(cpf_limpo) > 5) else (cns_limpo if len(cns_limpo) > 5 else None)
                
                if not identificador:
                    dt_nasc_hash = str(row.get('DT_NASC', ''))
                    hash_obj = hashlib.md5(f"{nome}{dt_nasc_hash}".encode())
                    identificador = str(int(hash_obj.hexdigest(), 16))[:15]

                # Status
                raw_motivo = str(row.get(col_motivo, '')).strip().split('.')[0]
                is_ativo = raw_motivo not in ['11', '12', '14', '15', '16', '18', '19', '31', '32', '51']

                # Paciente
                paciente, _ = Paciente.objects.update_or_create(
                    cns=identificador,
                    defaults={'nome': nome, 'ativo': is_ativo}
                )

                # --- 2. ONDE O ERRO DEVE ESTAR ---
                
                # Debug Data
                data_atend = row.get('DT_REALIZACAO')
                data_final = datetime.now().date()
                if isinstance(data_atend, datetime): 
                    data_final = data_atend.date()
                else:
                    try:
                        # Tenta converter string para data
                        data_str = str(data_atend).split(' ')[0]
                        data_final = datetime.strptime(data_str, '%d/%m/%Y').date()
                    except:
                        # Se falhar, usa hoje (para não quebrar o script)
                        pass

                # Debug Procedimento
                cod_acao = str(row.get('CO_ACAO', '000000')).split('.')[0]
                if cod_acao == 'nan' or cod_acao == '': 
                    cod_acao = '000000'

                procedimento, _ = Procedimento.objects.get_or_create(
                    codigo=cod_acao,
                    defaults={'nome': f"PROCEDIMENTO {cod_acao}"}
                )

                cns_prof = str(row.get('CO_CNS_MEDICO', '')).split('.')[0]
                
                # --- TENTATIVA DE CRIAÇÃO DO ATENDIMENTO ---
                # Verifica duplicidade
                if not Atendimento.objects.filter(
                    paciente=paciente,
                    procedimento=procedimento,
                    data=data_final,
                    profissional_cns=cns_prof
                ).exists():
                    Atendimento.objects.create(
                        paciente=paciente,
                        procedimento=procedimento,
                        data=data_final,
                        profissional_cns=cns_prof
                    )
                    # Se chegou aqui, funcionou!

            except Exception as e:
                # AQUI VAI MOSTRAR O ERRO
                count_erros += 1
                if count_erros <= 5: # Mostra só os 5 primeiros erros para não poluir
                    self.stdout.write(self.style.ERROR(f'ERRO NA LINHA {index}: {e}'))
                    self.stdout.write(f'Dados da linha: Data={row.get("DT_REALIZACAO")}, Proc={row.get("CO_ACAO")}')
                continue

        self.stdout.write(self.style.WARNING(f'Total de linhas com erro: {count_erros}'))