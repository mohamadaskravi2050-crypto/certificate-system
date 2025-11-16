import json
import base64
from io import BytesIO
import zipfile

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView

from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

from .models import PDFDocument, TextBox, FilledPDF


class HomeView(TemplateView):
    template_name = 'index.html'

class UploadView(TemplateView):
    template_name = 'upload.html'

class EditView(TemplateView):
    template_name = 'edit.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pdf_id'] = self.kwargs['pdf_id']
        return context

class FillView(TemplateView):
    template_name = 'fill.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pdf_id'] = self.kwargs['pdf_id']
        return context

class BatchFillView(TemplateView):
    template_name = 'batch_fill.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pdf_id'] = self.kwargs['pdf_id']
        return context


@csrf_exempt
def upload_pdf(request):
    if request.method == 'POST':
        if 'pdf_file' in request.FILES:
            pdf_file = request.FILES['pdf_file']
            name = request.POST.get('name', pdf_file.name)
            
            if not pdf_file.name.lower().endswith('.pdf'):
                return JsonResponse({'error': 'File must be a PDF'}, status=400)
            
            if pdf_file.size > 10 * 1024 * 1024:
                return JsonResponse({'error': 'File size must be less than 10MB'}, status=400)
            
            try:
                pdf_document = PDFDocument(name=name)
                pdf_document.set_pdf_data(pdf_file)
                pdf_document.save()
                
                return JsonResponse({
                    'id': pdf_document.id,
                    'name': pdf_document.name,
                    'message': 'PDF uploaded successfully'
                })
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)
        else:
            return JsonResponse({'error': 'No PDF file provided'}, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def edit_pdf(request, pdf_id):
    if request.method == 'GET':
        pdf_document = get_object_or_404(PDFDocument, id=pdf_id)
        
        text_boxes = pdf_document.text_boxes.all()
        text_boxes_data = [
            {
                'id': box.id,
                'name': box.name,
                'x': box.x_position,
                'y': box.y_position,
                'width': box.width,
                'height': box.height,
                'page': box.page_number,
                'font_size': box.font_size,
                'font_family': box.font_family
            }
            for box in text_boxes
        ]
        
        pdf_base64 = pdf_document.get_pdf_base64()
        
        return JsonResponse({
            'pdf_id': pdf_document.id,
            'pdf_name': pdf_document.name,
            'pdf_data': f"data:application/pdf;base64,{pdf_base64}",
            'text_boxes': text_boxes_data
        })
    
    elif request.method == 'POST':
        pdf_document = get_object_or_404(PDFDocument, id=pdf_id)
        try:
            data = json.loads(request.body)
            
            TextBox.objects.filter(pdf_document=pdf_document).delete()
            
            for box_data in data.get('text_boxes', []):
                TextBox.objects.create(
                    pdf_document=pdf_document,
                    name=box_data['name'],
                    x_position=box_data['x'],
                    y_position=box_data['y'],
                    width=box_data['width'],
                    height=box_data['height'],
                    page_number=box_data.get('page', 1),
                    font_size=box_data.get('font_size', 12),
                    font_family=box_data.get('font_family', 'Helvetica')
                )
            
            return JsonResponse({'message': 'Text boxes saved successfully'})
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

def generate_filled_pdf(pdf_document, values):
    try:
        
        original_pdf_data = pdf_document.get_pdf_data()
        original_pdf = PdfReader(BytesIO(original_pdf_data))
        
        
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=A4)
        
        
        for text_box in pdf_document.text_boxes.all():
            text_value = values.get(text_box.name, '')
            if text_value:
                
                if text_box.font_family == 'Helvetica':
                    can.setFont('Helvetica', text_box.font_size)
                elif text_box.font_family == 'Times-Roman':
                    can.setFont('Times-Roman', text_box.font_size)
                elif text_box.font_family == 'Courier':
                    can.setFont('Courier', text_box.font_size)
                else:
                    can.setFont('Helvetica', text_box.font_size)
                
                
                y_position = A4[1] - text_box.y_position - text_box.height
                can.drawString(text_box.x_position, y_position, text_value)
        
        can.save()
        packet.seek(0)
        new_pdf = PdfReader(packet)
        
       
        output = PdfWriter()
        
        for page_num in range(len(original_pdf.pages)):
            page = original_pdf.pages[page_num]
            if page_num == 0:  
                page.merge_page(new_pdf.pages[0])
            output.add_page(page)
        
        
        output_buffer = BytesIO()
        output.write(output_buffer)
        output_buffer.seek(0)
        
        return output_buffer.getvalue()
        
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        raise e

@csrf_exempt
def fill_pdf(request, pdf_id):
    if request.method == 'GET':
        pdf_document = get_object_or_404(PDFDocument, id=pdf_id)
        
        text_boxes = pdf_document.text_boxes.all()
        text_boxes_data = [
            {
                'id': box.id,
                'name': box.name,
                'label': box.name.replace('_', ' ').title(),
                'x': box.x_position,
                'y': box.y_position,
                'width': box.width,
                'height': box.height,
                'page': box.page_number,
                'font_size': box.font_size,
                'font_family': box.font_family
            }
            for box in text_boxes
        ]
        
        pdf_base64 = pdf_document.get_pdf_base64()
        
        return JsonResponse({
            'pdf_id': pdf_document.id,
            'pdf_name': pdf_document.name,
            'pdf_preview': f"data:application/pdf;base64,{pdf_base64}",
            'text_boxes': text_boxes_data
        })
    
    elif request.method == 'POST':
        pdf_document = get_object_or_404(PDFDocument, id=pdf_id)
        try:
            data = json.loads(request.body)
            filled_values = data.get('values', {})
            
            print(f"Generating PDF with values: {filled_values}")
            
           
            pdf_data = generate_filled_pdf(pdf_document, filled_values)
            
            
            if len(pdf_data) == 0:
                raise Exception('Generated PDF is empty')
            
            print(f"PDF generated successfully, size: {len(pdf_data)} bytes")
            
            
            FilledPDF.objects.create(
                pdf_document=pdf_document,
                filled_data=filled_values
            )
            
            
            response = HttpResponse(pdf_data, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="filled_{pdf_document.name}.pdf"'
            return response
        
        except Exception as e:
            print(f"Error in fill_pdf: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def batch_fill_pdf(request, pdf_id):
    if request.method == 'POST':
        pdf_document = get_object_or_404(PDFDocument, id=pdf_id)
        try:
            data = json.loads(request.body)
            entries = data.get('entries', [])
            
            print(f"Generating {len(entries)} PDFs in batch")
            
            
            zip_buffer = BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for i, entry_data in enumerate(entries):
                    values = entry_data.get('values', {})
                    title = entry_data.get('title', f'entry_{i+1}')
                    
                    print(f"Generating PDF {i+1}: {title}")
                    
                    
                    pdf_data = generate_filled_pdf(pdf_document, values)
                    
                   
                    file_name = f"{clean_filename(title)}_{i+1}.pdf"
                    zip_file.writestr(file_name, pdf_data)
                    
                    print(f"✅ PDF {i+1} added to ZIP: {file_name}")
            
            zip_buffer.seek(0)
            
            
            response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename="certificates_batch.zip"'
            return response
            
        except Exception as e:
            print(f"Error in batch_fill_pdf: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

def clean_filename(name):
    """Clean filename for safe use in ZIP"""
    return "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()

def list_pdfs(request):
    if request.method == 'GET':
        pdf_documents = PDFDocument.objects.all().order_by('-created_at')
        pdf_list = [
            {
                'id': pdf.id,
                'name': pdf.name,
                'created_at': pdf.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'text_boxes_count': pdf.text_boxes.count()
            }
            for pdf in pdf_documents
        ]
        
        return JsonResponse({'pdfs': pdf_list})
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def delete_textbox(request, textbox_id):
    if request.method == 'DELETE':
        text_box = get_object_or_404(TextBox, id=textbox_id)
        try:
            text_box.delete()
            return JsonResponse({'message': 'Text box deleted successfully'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)