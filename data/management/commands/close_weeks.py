from django.core.management.base import BaseCommand

from data.services import close_completed_weeks


class Command(BaseCommand):
    help = "Clôture et sauvegarde les semaines terminées ayant des opérations."

    def handle(self, *args, **options):
        close_completed_weeks()
        self.stdout.write(self.style.SUCCESS("Rapports hebdomadaires mis à jour."))
