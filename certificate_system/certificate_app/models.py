from django.db import models
import base64

class PDFDocument(models.Model):
    name = models.CharField(max_length=255)
    original_pdf = models.BinaryField()  # ذخیره به صورت binary با base64
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def set_pdf_data(self, pdf_file):
        # خواندن فایل و encode به base64
        pdf_data = pdf_file.read()
        self.original_pdf = base64.b64encode(pdf_data)
    
    def get_pdf_data(self):
        # decode از base64 و بازگرداندن داده‌های اصلی
        return base64.b64decode(self.original_pdf)
    
    def get_pdf_base64(self):
        # بازگرداندن داده‌های base64 برای نمایش در فرانت‌اند
        return self.original_pdf.decode('utf-8')
    
    def __str__(self):
        return self.name

class TextBox(models.Model):
    pdf_document = models.ForeignKey(PDFDocument, on_delete=models.CASCADE, related_name='text_boxes')
    name = models.CharField(max_length=100)
    x_position = models.FloatField()
    y_position = models.FloatField()
    width = models.FloatField()
    height = models.FloatField()
    page_number = models.IntegerField(default=1)
    font_size = models.IntegerField(default=12)
    font_family = models.CharField(max_length=50, default='Helvetica')
    
    def __str__(self):
        return f"{self.name} - {self.pdf_document.name}"

class FilledPDF(models.Model):
    pdf_document = models.ForeignKey(PDFDocument, on_delete=models.CASCADE)
    filled_data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Filled {self.pdf_document.name}"