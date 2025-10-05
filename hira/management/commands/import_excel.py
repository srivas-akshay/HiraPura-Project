from django.core.management.base import BaseCommand
import pandas as pd
from hira.models import Contact
import math

class Command(BaseCommand):
    help = "Import data from Excel file into Contact model"

    def add_arguments(self, parser):
        parser.add_argument('excel_path', type=str, help='Path to Excel file')

    def safe_str(self, value):
        """Convert value to string and strip, handle NaN/None."""
        if value is None or (isinstance(value, float) and math.isnan(value)):
            return ''
        return str(value).strip()

    def handle(self, *args, **kwargs):
        path = kwargs['excel_path']
        df = pd.read_excel(path)

        # Clean column names
        df.columns = [col.strip() for col in df.columns]

        for index, row in df.iterrows():
            try:
                contact, created = Contact.objects.update_or_create(
                    whatsapp_no=self.safe_str(row.get('Whatsapp Mobile Number')),
                    defaults={
                        'full_name': self.safe_str(row.get('Full Name')),
                        'sub_cast': self.safe_str(row.get('Subcast')),
                        'address': self.safe_str(row.get('Address')),
                        'area': self.safe_str(row.get('Area')),
                        'zone': self.safe_str(row.get('Zone')),
                        'alternate_no': self.safe_str(row.get('Alternative Mobile Number')) or None,
                        'family_members': int(row.get('Family Members') or 0),
                        'email': self.safe_str(row.get('Email')) or None,
                        'vip': False
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f"✅ Imported row {index + 2}: {contact.full_name}"))
                else:
                    self.stdout.write(self.style.WARNING(f"⚠️ Updated row {index + 2}: {contact.full_name}"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error with row {index + 2}: {e}"))
