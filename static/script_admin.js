document.addEventListener('DOMContentLoaded', function() {
    //  Код переключения страниц
    const pageNumbers = document.querySelectorAll('.page-number');
    const pages = document.querySelectorAll('.page');
    const deletePageForm = document.getElementById('delete-page-form');
    const deletePageIndexInput = document.getElementById('delete-page-index');

    // Функция для обновления индекса страницы для удаления
    function updateDeletePageIndex(pageIndex) {
        if (deletePageIndexInput) { // Проверка, существует ли элемент
            deletePageIndexInput.value = pageIndex; // Устанавливаем индекс страницы для удаления
        }
        if (deletePageForm) {
             if (pageIndex == 1) {
                deletePageForm.style.display = 'none'; // Скрываем кнопку
             }
            else{
                deletePageForm.style.display = 'block'; // Показываем кнопку
            }
        }
    }

    pageNumbers.forEach(pageNumber => {
        pageNumber.addEventListener('click', function() {
            const pageToShow = this.dataset.page;

            // Скрыть все страницы
            pages.forEach(page => {
                page.style.display = 'none';
            });

            // Показать выбранную страницу
            document.getElementById(`page-${pageToShow}`).style.display = 'block';

            // Убрать класс 'active' у всех номеров страниц
            pageNumbers.forEach(number => {
                number.classList.remove('active');
            });

            // Добавить класс 'active' к выбранному номеру страницы
            this.classList.add('active');

            // Обновляем номер страницы для удаления
            updateDeletePageIndex(parseInt(pageToShow));
        });
    });

    // Инициализируем номер страницы для удаления при загрузке
    if (pageNumbers.length > 0) {
        updateDeletePageIndex(1); // 1 - это индекс первой страницы
    }
});