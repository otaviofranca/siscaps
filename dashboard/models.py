from datetime import timedelta
from django.db import models
from django.db.models import Max
from django.utils import timezone


class PacienteManager(models.Manager):
    """Facilita buscas em massa por pacientes ativos/inativos"""
    def atualizar_todos_status(self):
        limite = timezone.now().date() - timedelta(days=90)
        

        ativos_ids = Atendimento.objects.filter(
            data__gte=limite
        ).values_list('paciente_id', flat=True).distinct()
        

        self.update(ativo=False) 
        self.filter(id__in=ativos_ids).update(ativo=True)

class Paciente(models.Model):
    cpf = models.CharField(max_length=11, unique=True, null=True, blank=True)
    # CNS deixa de ser unique para não dar erro quando vier zerado
    cns = models.CharField(max_length=15, null=True, blank=True) 
    nome = models.CharField(max_length=255)
    nome_mae = models.CharField(max_length=255, null=True, blank=True)

    data_nascimento=models.DateField(null=True, blank=True)
    sexo = models.CharField(max_length=10, blank=True, null=True)
    raca_cor = models.CharField(max_length=5, blank=True, null=True)

    municipio_codigo = models.CharField(max_length=10, blank=True, null=True)
    endereco = models.TextField(blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)

    cep = models.CharField(max_length=9, null=True, blank=True) 
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    em_situacao_rua = models.BooleanField(default=False)
    usuario_alcool_drogas = models.BooleanField(default=False)

    ativo = models.BooleanField(default=True)
    
    objects = PacienteManager() 
    @property
    def status_atividade(self):
        """Lógica dinâmica para exibição na tela"""
        ultimo_atendimento = self.atendimento_set.aggregate(Max('data'))['data__max']
        if not ultimo_atendimento:
            return "Sem Atendimento"
            
        limite = timezone.now().date() - timedelta(days=90)
        return "Ativo" if ultimo_atendimento >= limite else "Inativo"
    
    def __str__(self):
        return f"{self.nome} - {self.cns}"
    
class Procedimento(models.Model):
    # Aumentei o tamanho do código para garantir
    codigo = models.CharField(max_length=20, unique=True)
    nome = models.CharField(max_length=500)
    valor = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Novos campos para guardar os detalhes da planilha
    descricao = models.TextField(null=True, blank=True)
    cbo = models.TextField(null=True, blank=True)
    cid = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.codigo} - {self.nome}"
    
class Atendimento(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    procedimento = models.ForeignKey(Procedimento, on_delete=models.CASCADE)

    cid = models.CharField(max_length=10, null=True, blank=True)
    carater_atendimento = models.CharField(max_length=5, null=True, blank=True)

    profissional_cns = models.CharField(max_length=20, blank=True, null=True)
    cbo = models.CharField(max_length=10, blank=True, null=True)
    data = models.DateField()

    def __str__(self):
        return f"{self.paciente} - {self.procedimento} - {self.data}"