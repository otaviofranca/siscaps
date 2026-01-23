import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker
from dashboard.models import Paciente, Procedimento, Atendimento

class Command(BaseCommand):
    help = 'Popula o banco de dados com dados fictícios para testes'

    def handle(self, *args, **kwargs):
        fake = Faker('pt_BR') # Gera dados em Português do Brasil
        
        self.stdout.write(self.style.WARNING('Iniciando a criação de dados...'))

        # ==========================================
        # 1. CRIAR PROCEDIMENTOS (Dados Reais SUS)
        # ==========================================
        lista_procedimentos = [
            {'cod': '0301010072', 'nome': 'CONSULTA MEDICA EM ATENÇÃO ESPECIALIZADA', 'valor': 10.00},
            {'cod': '0301010048', 'nome': 'CONSULTA DE PROFISSIONAIS DE NIVEL SUPERIOR', 'valor': 6.30},
            {'cod': '0301080208', 'nome': 'ATENDIMENTO INDIVIDUAL EM PSICOTERAPIA', 'valor': 12.50},
            {'cod': '0301080232', 'nome': 'ATENDIMENTO EM GRUPO', 'valor': 15.00},
            {'cod': '0301080194', 'nome': 'ACOLHIMENTO NOTURNO', 'valor': 85.00},
            {'cod': '0301080020', 'nome': 'ATENDIMENTO FAMILIAR', 'valor': 10.00},
        ]

        procedimentos_objs = []
        for proc in lista_procedimentos:
            obj, created = Procedimento.objects.get_or_create(
                codigo=proc['cod'],
                defaults={'nome': proc['nome'], 'valor': proc['valor']}
            )
            procedimentos_objs.append(obj)
        
        self.stdout.write(self.style.SUCCESS(f'{len(procedimentos_objs)} Procedimentos verificados/criados.'))

        # ==========================================
        # 2. CRIAR PACIENTES (50 Pacientes)
        # ==========================================
        pacientes_objs = []
        for _ in range(50):
            # Gera um CNS falso de 15 dígitos
            cns_fake = fake.numerify(text='###############')
            
            # Evita erro se o CNS já existir (raro, mas possível)
            paciente, created = Paciente.objects.get_or_create(
                cns=cns_fake,
                defaults={
                    'nome': fake.name(),
                    'ativo': random.choice([True, True, True, False]) # 75% de chance de estar ativo
                }
            )
            if created:
                pacientes_objs.append(paciente)

        self.stdout.write(self.style.SUCCESS(f'{len(pacientes_objs)} novos pacientes criados.'))

        # Recarrega todos os pacientes (incluindo antigos se houver)
        todos_pacientes = list(Paciente.objects.all())

        # ==========================================
        # 3. CRIAR ATENDIMENTOS (RAAS) - 2.000 Registros
        # ==========================================
        # Gera atendimentos distribuídos nos últimos 12 meses
        atendimentos = []
        profissionais = [fake.name() for _ in range(5)] # Cria 5 nomes de médicos/psicólogos fixos
        
        data_hoje = timezone.now().date()
        data_inicio = data_hoje - timedelta(days=365)

        for _ in range(2000):
            # Escolha aleatória
            paciente = random.choice(todos_pacientes)
            procedimento = random.choice(procedimentos_objs)
            profissional = random.choice(profissionais)
            
            # Data aleatória entre hoje e 1 ano atrás
            dias_aleatorios = random.randint(0, 365)
            data_atendimento = data_inicio + timedelta(days=dias_aleatorios)

            atendimento = Atendimento(
                paciente=paciente,
                procedimento=procedimento,
                profissional=profissional,
                data=data_atendimento
            )
            atendimentos.append(atendimento)

        # Bulk create é muito mais rápido que salvar um por um
        Atendimento.objects.bulk_create(atendimentos)

        self.stdout.write(self.style.SUCCESS(f'SUCESSO! {len(atendimentos)} atendimentos gerados.'))