let map;
let polygonLayer;
let markerLayer;
let currentPageIndex = 0; // Объявляем currentPageIndex глобально
let currentStreetData = null; // Глобальная переменная для хранения streetData

function initMap() {
    map = L.map('map').setView([53.455, 56.035], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
    polygonLayer = L.layerGroup().addTo(map);
    markerLayer = L.layerGroup().addTo(map);
}

function displayStreetOnMap(streetData) {
    let address;
    let lat, lon;

    polygonLayer.clearLayers();
    markerLayer = L.layerGroup().addTo(map);

    if (streetData.lat && streetData.lon) {
        lat = parseFloat(streetData.lat); //Added parseFloat for safety
        lon = parseFloat(streetData.lon); //Added parseFloat for safety
        address = streetData.name;
        console.log("Используем координаты из JSON для адреса:", address);

        L.marker([lat, lon]).addTo(markerLayer)
            .bindPopup(address)
            .openPopup();
        map.setView([lat, lon], 15);
    } else {
        if (streetData.nominatimQuery) {
            address = streetData.nominatimQuery + " г. Ишимбай";
        } else {
            address = streetData.name + " г. Ишимбай";
        }
        console.log("Отправляем запрос к Nominatim для адреса:", address);

        fetch('https://nominatim.openstreetmap.org/search?format=json&polygon_geojson=1&limit=1&q=' + encodeURIComponent(address))
            .then(response => response.json())
            .then(data => {
                console.log("Nominatim вернул:", data);
                if (data && data.length > 0) {
                    processNominatimData(data, address);
                } else {
                    console.log("Адрес не найден Nominatim.");
                }
            })
            .catch(err => {
                console.error("Ошибка при запросе к Nominatim:", err);
            });
    }
}

function processNominatimData(data, address) {
    var lat = parseFloat(data[0].lat); //Added parseFloat for safety
    var lon = parseFloat(data[0].lon); //Added parseFloat for safety
    var geojson = data[0].geojson;

    L.marker([lat, lon]).addTo(markerLayer)
        .bindPopup(address)
        .openPopup();

    map.setView([lat, lon], 15);

    if (geojson) {
        L.geoJSON(geojson, {
            style: {
                fillColor: 'yellow',
                color: 'orange',
                weight: 3,
                opacity: 0.8,
                fillOpacity: 0.4,
            }
        }).addTo(polygonLayer);
    } else {
        console.log("Геометрия улицы не найдена.");
    }
}

function openStreetInfo(streetData) {
    const streetInfoContainer = document.getElementById('streetInfoContainer');
    const streetInfoContent = document.getElementById('streetInfoContent');
    streetInfoContainer.style.display = "block";

    currentStreetData = streetData; // Сохраняем текущие данные об улице
    currentPageIndex = 0; // Сбрасываем индекс страницы при открытии новой улицы

    if (streetData && streetData.pages && streetData.pages.length > 0) {
        displayPage(streetData, currentPageIndex);
    } else {
        streetInfoContent.innerHTML = `<p>Нет информации для отображения.</p>`;
    }

    displayStreetOnMap(streetData);

    const prevButton = document.getElementById('prevPageButton');
    const nextButton = document.getElementById('nextPageButton');

    prevButton.addEventListener('click', previousPage);
    nextButton.addEventListener('click', nextPage);
}

function displayPage(streetData, pageIndex) {
    console.log("displayPage function called");
    console.log("pageIndex:", pageIndex);

    if (!streetData || !streetData.pages || pageIndex < 0 || pageIndex >= streetData.pages.length) {
        return;
    }

    const page = streetData.pages[pageIndex];
    const imgSrc = page.photo ? "/static/" + page.photo : ""; 
    const imgAlt = streetData.name || "Изображение";

    streetInfoContent.innerHTML = `
        <h2>${page.title || "Заголовок"}</h2>
        <img id="pageImage" src="${imgSrc}" alt="${imgAlt}" style="max-width: 150px; max-height: 250px; object-fit: cover;"> 
        <p>${page.content || "Контент"}</p>
        <div class="page-buttons">
            <button id="prevPageButton" ${pageIndex <= 0 ? 'disabled' : ''}>Предыдущая</button>
            <span>Страница ${pageIndex + 1} из ${streetData.pages.length}</span>
            <button id="nextPageButton" ${pageIndex === streetData.pages.length - 1 ? 'disabled' : ''}>Следующая</button>
        </div>
    `;

    // Назначаем обработчики кнопкам после рендеринга
    document.getElementById('prevPageButton').addEventListener('click', previousPage);
    document.getElementById('nextPageButton').addEventListener('click', nextPage);
}

function displayStreets(streetsData) {
    const streetList = document.getElementById('streetList');
    streetList.innerHTML = '';
    
    if (streetsData) {
        // Разделяем улицы на важные и остальные
        const importantStreets = streetsData.filter(street => street.class === "Важное");
        const otherStreets = streetsData.filter(street => street.class !== "Важное");

        // Сортируем другие улицы по алфавиту
        otherStreets.sort((a, b) => a.name.localeCompare(b.name));

        // Объединяем важные улицы с отсортированными остальными
        const sortedStreets = [...importantStreets, ...otherStreets];

        // Отображаем отсортированные улицы
        sortedStreets.forEach(street => {
            let li = document.createElement('li');
            let displayName = "";
            let imageHTML = "";

            if (street.class === "Важное" && street.photo) {
                imageHTML = `<img src="/static/img/vasno.png" alt="Важное" style="width: 20px; height: 20px; margin-right: 5px; vertical-align: middle;">`;
            }

            if (street.class === "Школа" && street.photo) {
                imageHTML = `<img src="/static/img/school.png" alt="Школа" style="width: 20px; height: 20px; margin-right: 5px; vertical-align: middle;">`;
            }

            if (street.class === "Прочее" && street.photo) {
                imageHTML = `<img src="/static/img/.png" alt="Прочее" style="width: 20px; height: 20px; margin-right: 5px; vertical-align: middle;">`;
            }

            if (street.type === "Улица") {
                imageHTML = `<img src="/static/img/road.png" alt="Улица" style="width: 20px; height: 20px; margin-right: 5px; vertical-align: middle;">`;
                displayName = street.name;
            } else {
                if (street.name.includes(street.type)) {
                    displayName = street.name;
                } else {
                    displayName = `${street.type} ${street.name}`;
                }
            }

            li.innerHTML = imageHTML + displayName;
            li.addEventListener('click', () => openStreetInfo(street));
            streetList.appendChild(li);
        });
    }
}
function setupSearch() {
    const searchInput = document.getElementById('searchInput');
    searchInput.addEventListener('input', function(e) {
        const searchTerm = e.target.value.toLowerCase();
        const filteredStreets = streetsData.filter(street => {
            if (street && street.name) {
                const displayName = (street.type === "Улица") ? `${street.name}` : `${street.type} ${street.name}`;
                return displayName.toLowerCase().includes(searchTerm);
            }
            return false;
        });
        displayStreets(filteredStreets);
    });
}

function setMapHeight() {
    const mapContainer = document.getElementById('map-container');
    const mapWidth = mapContainer.offsetWidth;
    mapContainer.style.height = mapWidth + 'px';
    if (map) {
        map.invalidateSize();
    }
}

document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const streetInfoContainer = document.getElementById('streetInfoContainer');
        if (streetInfoContainer && streetInfoContainer.style.display === 'block') {
            streetInfoContainer.style.display = 'none';
        }
    }
});

function makeModalDraggable() {
    let isDragging = false;
    let dragStartX = 0;
    let dragStartY = 0;

    const streetInfoContainer = document.getElementById('streetInfoContainer');
    const modalHeader = document.getElementById('modalHeader');

    modalHeader.addEventListener('mousedown', function(event) {
        isDragging = true;
        dragStartX = event.clientX - streetInfoContainer.offsetLeft;
        dragStartY = event.clientY - streetInfoContainer.offsetTop;
        modalHeader.style.cursor = 'grabbing';
    });

    document.addEventListener('mouseup', function() {
        isDragging = false;
        modalHeader.style.cursor = 'grab';
    });

    document.addEventListener('mousemove', function(event) {
        if (!isDragging) return;
        streetInfoContainer.style.left = (event.clientX - dragStartX) + 'px';
        streetInfoContainer.style.top = (event.clientY - dragStartY) + 'px';
    });
}

function previousPage() {
    console.log("previousPage function called"); // Добавлено
    console.log("currentPageIndex before decrement:", currentPageIndex); // Добавлено
    currentPageIndex--;
    console.log("currentPageIndex after decrement:", currentPageIndex); // Добавлено
    displayPage(currentStreetData, currentPageIndex);
}

function nextPage() {
    console.log("nextPage: currentPageIndex =", currentPageIndex); // Добавляем console.log
    currentPageIndex++;
    displayPage(currentStreetData, currentPageIndex);
}

document.addEventListener('DOMContentLoaded', function() {
    initMap();
    setMapHeight();
    makeModalDraggable();

    // streetsData уже доступна из index.html
    displayStreets(streetsData);
    setupSearch();

    //  Добавляем код переключения страниц сюда!  ********************
    const pageNumbers = document.querySelectorAll('.page-number');
    const pages = document.querySelectorAll('.page');

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
        });
    });

});
