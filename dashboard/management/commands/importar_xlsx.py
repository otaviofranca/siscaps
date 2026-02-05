import pandas as pd
import os
import hashlib
import numpy as np
import time
from datetime import datetime, date
from django.core.management.base import BaseCommand
from django.conf import settings
from dashboard.models import Paciente, Procedimento, Atendimento
from geopy.geocoders import Nominatim

class Command(BaseCommand):
    help = 'Importação RAAS/BPA com Geocodificação Inteligente (Cache de CEP)'

    def handle(self, *args, **kwargs):
        arquivo = os.path.join(settings.BASE_DIR, 'dados_caps.xls')
        self.stdout.write(self.style.WARNING(f'Lendo arquivo: {arquivo}'))

        try:
            df = pd.read_excel(arquivo, engine='openpyxl')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro ao ler arquivo: {e}'))
            return

        df.columns = df.columns.str.strip().str.upper()
        colunas = list(df.columns)

        geolocator = Nominatim(user_agent="siscaps_teresina_v2")

        col_cid_principal = 'CO_CID_PRINCIPAL' if 'CO_CID_PRINCIPAL' in colunas else None
        col_cid_causas = 'CO_CID_CAUSAS' if 'CO_CID_CAUSAS' in colunas else None
        if not col_cid_principal:
             col_cid_principal = next((c for c in colunas if 'CID' in c and 'PRINCIPAL' in c), None)
        
        col_data = next((c for c in colunas if 'DT_REALIZACAO' in c or 'DATA_ATEND' in c), None)
        if not col_data: col_data = next((c for c in colunas if 'DATA' in c), None)
        
        col_droga = next((c for c in colunas if 'DROGA' in c), None)
        col_cep = next((c for c in colunas if 'CEP' in c), None)

        if not col_data:
            self.stdout.write(self.style.ERROR('ERRO: Coluna de Data não encontrada.'))
            return

        count_processados = 0
        
        # cahe local
        cache_local_coordenadas = {}

        for index, row in df.iterrows():
            try:
                raw_data = row[col_data]
                data_final = None
                if isinstance(raw_data, (datetime, date)):
                    data_final = raw_data
                else:
                    str_data = str(raw_data).strip()
                    try: data_final = datetime.strptime(str_data[:10], '%d/%m/%Y').date()
                    except:
                        try: data_final = datetime.strptime(str_data[:10], '%Y-%m-%d').date()
                        except: pass
                
                if not data_final: continue

                nome = str(row.get('NM_PACIENTE', 'Desconhecido')).strip().upper()
                if nome in ['', 'NAN', 'NAT']: continue

                cpf = ''.join(filter(str.isdigit, str(row.get('CO_CPF_PACIENTE', ''))))
                cns = ''.join(filter(str.isdigit, str(row.get('CO_CNS_PACIENTE', ''))))
                identificador = cpf if len(cpf) > 5 else (cns if len(cns) > 5 else None)
                
                if not identificador:
                    dt_hash = str(row.get('DT_NASC', ''))
                    hash_obj = hashlib.md5(f"{nome}{dt_hash}".encode())
                    identificador = str(int(hash_obj.hexdigest(), 16))[:15]

                # 3. logica geocodificacao com cache
                lat, lng = None, None
                cep_formatado = None

                if col_cep:
                    cep_raw = str(row[col_cep]).strip().replace('-', '')
                    cep_limpo = ''.join(filter(str.isdigit, cep_raw))
                    
                    if len(cep_limpo) >= 8:
                        cep_formatado = cep_limpo[:8]
                        
                        if cep_formatado in cache_local_coordenadas:
                            lat, lng = cache_local_coordenadas[cep_formatado]
                        else:
                            p_existente = Paciente.objects.filter(
                                cep=cep_formatado, 
                                latitude__isnull=False
                            ).first()

                            if p_existente:
                                lat, lng = p_existente.latitude, p_existente.longitude
                                cache_local_coordenadas[cep_formatado] = (lat, lng)
                            else:
                                try:
                                    location = geolocator.geocode(f"{cep_formatado}, Teresina, Brasil", timeout=10)
                                    if location:
                                        lat, lng = location.latitude, location.longitude
                                        cache_local_coordenadas[cep_formatado] = (lat, lng)
                                        # Delay obrigatorio por causa da API
                                        time.sleep(1) 
                                except:
                                    pass

                is_droga = False
                if col_droga:
                    val_droga = str(row[col_droga]).upper()
                    if val_droga in ['S', 'SIM', '1', 'SA', 'SC', 'SO', 'SACO']: is_droga = True

                paciente, _ = Paciente.objects.update_or_create(
                    cns=identificador,
                    defaults={
                        'nome': nome, 
                        'usuario_alcool_drogas': is_droga, 
                        'cep': cep_formatado, 
                        'latitude': lat,
                        'longitude': lng,
                        'ativo': True
                    }
                )

                cid_final = "Z00" 
                if col_cid_principal:
                    val = str(row[col_cid_principal]).strip().upper()
                    if val not in ['NAN', 'NONE', '', 'NAT', 'NULL']:
                        cid_final = val
                
                if (cid_final == "Z00" or cid_final == "") and col_cid_causas:
                    val_sec = str(row[col_cid_causas]).strip().upper()
                    if val_sec not in ['NAN', 'NONE', '', 'NAT', 'NULL']:
                        cid_final = val_sec

                cod_proc = str(row.get('CO_ACAO', '000000')).split('.')[0]
                procedimento, _ = Procedimento.objects.get_or_create(
                    codigo=cod_proc, 
                    defaults={'nome': f'PROC {cod_proc}', 'valor': 0}
                )
                
                cns_prof = str(row.get('CO_CNS_MEDICO', '')).split('.')[0]

                Atendimento.objects.update_or_create(
                    paciente=paciente,
                    data=data_final,
                    procedimento=procedimento,
                    profissional_cns=cns_prof,
                    defaults={'cid': cid_final} 
                )

                count_processados += 1
                if count_processados % 100 == 0:
                    self.stdout.write(f'Processados: {count_processados}...')

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Erro ao processar linha {index + 2}: {e}'))
                continue

        self.stdout.write(self.style.SUCCESS(f'Concluído! {count_processados} registros atualizados com sucesso.'))