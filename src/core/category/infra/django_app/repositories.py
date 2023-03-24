# pylint: disable=no-member,unexpected-keyword-arg
from typing import List, Type, TYPE_CHECKING
from django.core import exceptions as django_exceptions
from django.core.paginator import Paginator
from core.__seedwork.domain.exceptions import NotFoundException
from core.__seedwork.domain.value_objects import UniqueEntityId
from core.category.domain.entities import Category
from core.category.domain.repositories import CategoryRepository
from core.category.infra.django_app.mappers import CategoryModelMapper


if TYPE_CHECKING:
    from core.category.infra.django_app.models import CategoryModel


class CategoryDjangoRepository(CategoryRepository):

    sortable_fields: List[str] = ['name', 'created_at']
    model: Type['CategoryModel']

    def __init__(self) -> None:
        from core.category.infra.django_app.models import CategoryModel  # pylint: disable=import-outside-toplevel
        self.model = CategoryModel

    def insert(self, entity: Category) -> None:
        model = CategoryModelMapper.to_model(entity)
        model.save()

    def bulk_insert(self, entities: List[Category]) -> None:
        self.model.objects.bulk_create(
            list(
                map(
                    CategoryModelMapper.to_model, entities
                )
            )
        )

    def find_by_id(self, entity_id: str | UniqueEntityId) -> Category:
        id_str = str(entity_id)
        model = self._get(id_str)
        return CategoryModelMapper.to_entity(model)

    def find_all(self) -> List[Category]:
        return [CategoryModelMapper.to_entity(model) for model in self.model.objects.all()]

    def update(self, entity: Category) -> None:
        self._get(entity.id)
        model = CategoryModelMapper.to_model(entity)
        model.save()

    def delete(self, entity_id: str | UniqueEntityId) -> None:
        id_str = str(entity_id)
        model = self._get(id_str)
        model.delete()

    def _get(self, entity_id: str) -> 'CategoryModel':
        try:
            return self.model.objects.get(pk=entity_id)
        except (self.model.DoesNotExist, django_exceptions.ValidationError) as exception:
            raise NotFoundException(
                f"Entity not found using ID '{entity_id}'") from exception

    def search(self, input_params: CategoryRepository.SearchParams) -> CategoryRepository.SearchResult:
        query = self.model.objects.all()

        if input_params.filter:
            query = query.filter(name__icontains=input_params.filter)
        if input_params.sort and input_params.sort in self.sortable_fields:
            query = query.order_by(
                input_params.sort if input_params.sort_dir == 'asc' else f'-{input_params.sort}'
            )
        else:
            query = query.order_by('-created_at')

        paginator = Paginator(query, input_params.per_page)
        page_obj = paginator.page(input_params.page)

        return CategoryRepository.SearchResult(
            items=[CategoryModelMapper.to_entity(
                model) for model in page_obj.object_list],
            total=paginator.count,
            current_page=input_params.page,
            per_page=input_params.per_page,
            sort=input_params.sort,
            sort_dir=input_params.sort_dir,
            filter=input_params.filter
        )
