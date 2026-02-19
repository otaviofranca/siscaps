from django.core.management.base import BaseCommand
from dashboard.models import Paciente

class Command(BaseCommand):
    help = 'Atualiza o status ativo/inativo dos pacientes (90 dias)'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Atualizando status...'))
        Paciente.objects.atualizar_todos_status()
        
        ativos = Paciente.objects.filter(ativo=True).count()
        inativos = Paciente.objects.filter(ativo=False).count()
        
        self.stdout.write(self.style.SUCCESS(f'✓ Pacientes ativos: {ativos}'))
        self.stdout.write(self.style.SUCCESS(f'✓ Pacientes inativos: {inativos}'))