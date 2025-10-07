from django.db import models
from django.utils import timezone


class Server(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self) -> str:
        return self.name


class System(models.Model):
    name = models.CharField(max_length=255, unique=True)
    url = models.URLField(max_length=200)
    server = models.ForeignKey(Server, on_delete=models.CASCADE, related_name="systems")

    def __str__(self) -> str:
        return self.name


class SystemStatus(models.Model):
    system = models.OneToOneField(System, on_delete=models.CASCADE, related_name="current_status")
    status = models.CharField(max_length=20)
    status_code = models.IntegerField(null=True, blank=True)
    checked_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["system__name"]

    def __str__(self) -> str:
        return f"{self.system.name}: {self.status}"


class SystemStatusHistory(models.Model):
    system = models.ForeignKey(System, on_delete=models.CASCADE, related_name="status_history")
    status = models.CharField(max_length=20)
    status_code = models.IntegerField(null=True, blank=True)
    checked_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-checked_at"]

    def __str__(self) -> str:
        return f"{self.system.name} @ {self.checked_at:%Y-%m-%d %H:%M:%S}: {self.status}"


class SystemDowntime(models.Model):
    system = models.ForeignKey(System, on_delete=models.CASCADE, related_name="downtimes")
    status = models.CharField(max_length=20)
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self) -> str:
        end = self.ended_at.strftime("%Y-%m-%d %H:%M:%S") if self.ended_at else "em aberto"
        return f"{self.system.name} ({self.status}) de {self.started_at:%Y-%m-%d %H:%M:%S} até {end}"

    @property
    def duration(self):
        end_time = self.ended_at or timezone.now()
        return end_time - self.started_at
