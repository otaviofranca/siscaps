from django.core.management.base import BaseCommand
from dashboard.models import Procedimento

class Command(BaseCommand):
    help = 'Popula a tabela de procedimentos com os códigos mais comuns de CAPS (Mini-SIGTAP)'

    def handle(self, *args, **kwargs):
        # Lista com os principais procedimentos de Saúde Mental (CAPS)
        # Fonte: Tabela Unificada SIGTAP
        sigtap_caps = [
            # --- CONSULTAS E ATENDIMENTOS INDIVIDUAIS ---
            {'cod': '0301010072', 'nome': 'CONSULTA MEDICA EM ATENCAO ESPECIALIZADA', 'valor': 10.00},
            {'cod': '0301010048', 'nome': 'CONSULTA DE PROFISSIONAIS DE NIVEL SUPERIOR NA ATENCAO ESPECIALIZADA', 'valor': 6.30},
            {'cod': '0301080208', 'nome': 'ATENDIMENTO INDIVIDUAL EM PSICOTERAPIA', 'valor': 12.50},
            {'cod': '0301080216', 'nome': 'ATENDIMENTO INDIVIDUAL EM PSICOTERAPIA (REABILITACAO)', 'valor': 12.50},
            {'cod': '0301080020', 'nome': 'ATENDIMENTO FAMILIAR EM CAPS', 'valor': 10.00},
            {'cod': '0301080224', 'nome': 'ATENDIMENTO FAMILIAR EM CAPS', 'valor': 10.00},
            # --- GRUPOS E OFICINAS ---
            {'cod': '0301080232', 'nome': 'ATENDIMENTO EM GRUPO EM CAPS', 'valor': 15.00},
            {'cod': '0301080240', 'nome': 'ATENDIMENTO EM OFICINA TERAPEUTICA EM CAPS', 'valor': 15.00},
            {'cod': '0301080259', 'nome': 'ACOLHIMENTO DIURNO EM CAPS', 'valor': 25.00},
            {'cod': '0301080283', 'nome': 'ACOLHIMENTO INICIAL EM CAPS', 'valor': 10.00},
            {'cod': '0301080194', 'nome': 'ACOLHIMENTO NOTURNO EM CAPS', 'valor': 95.00},
            
            # --- SITUAÇÕES DE CRISE E URGÊNCIA ---
            {'cod': '0301080275', 'nome': 'ATENDIMENTO A SITUACOES DE CRISE', 'valor': 15.00},
            {'cod': '0301060061', 'nome': 'ATENDIMENTO DE URGENCIA EM ATENCAO ESPECIALIZADA', 'valor': 20.00},

            # --- EXTERNOS ---
            {'cod': '0301080291', 'nome': 'ATENDIMENTO DOMICILIAR PARA PACIENTES DE CAPS', 'valor': 20.00},
            {'cod': '0301080135', 'nome': 'PRATICAS CORPORAIS EM CAPS', 'valor': 6.30},
            {'cod': '0301080127', 'nome': 'PRATICAS EXPRESSIVAS E COMUNICATIVAS EM CAPS', 'valor': 6.30},
        ]

        self.stdout.write(self.style.WARNING('Atualizando nomes dos procedimentos...'))
        
        atualizados = 0
        criados = 0

        for item in sigtap_caps:
            # O update_or_create é perfeito aqui: se existe o código, ele só corrige o nome.
            # Se não existe, ele cria um novo.
            obj, created = Procedimento.objects.update_or_create(
                codigo=item['cod'], 
                defaults={          
                    'nome': item['nome'],
                    'valor': item['valor']
                }
            )
            
            # Tenta também atualizar versões do código sem o zero à esquerda (comum no Excel)
            # Ex: Se no banco está "301080216", atualizamos para o nome correto também.
            cod_sem_zero = item['cod'].lstrip('0')
            Procedimento.objects.filter(codigo=cod_sem_zero).update(
                nome=item['nome'], 
                valor=item['valor']
            )

            if created:
                criados += 1
            else:
                atualizados += 1

        self.stdout.write(self.style.SUCCESS(f'Concluído! {criados} novos criados e {atualizados} atualizados.'))