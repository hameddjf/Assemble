from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404

from .models import Category

# Create your views here.


class CategoryListView(ListView):
    model = Category
    template_name = 'categories/category_list.html'
    context_object_name = 'categories'
    paginate_by = 12

    def get_queryset(self):
        return Category.objects.filter(is_active=True, parent=None)


class CategoryDetailView(DetailView):
    model = Category
    template_name = 'categories/category_detail.html'
    context_object_name = 'category'

    def get_object(self):
        return get_object_or_404(
            Category,
            slug=self.kwargs['slug'],
            is_active=True
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subcategories'] = self.object.children.filter(is_active=True)
        return context
