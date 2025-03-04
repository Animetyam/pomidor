// Создаём контейнер для помидоров (добавляется один раз)
let tomatoContainer = document.createElement("div");
tomatoContainer.style.position = "fixed";
tomatoContainer.style.top = "0";
tomatoContainer.style.left = "0";
tomatoContainer.style.width = "100%";
tomatoContainer.style.height = "100%";
tomatoContainer.style.pointerEvents = "none";
tomatoContainer.style.zIndex = "-1"; // Помещаем за все элементы
document.body.appendChild(tomatoContainer);

function createFallingTomato() {
    const tomato = document.createElement("img");
    tomato.src = "/static/red1.png"; // Укажите путь к изображению
    tomato.style.position = "absolute";
    tomato.style.left = Math.random() * window.innerWidth + "px";
    tomato.style.top = "-50px";
    tomato.style.width = "40px";
    tomato.style.height = "40px";
    tomato.style.pointerEvents = "none";

    tomatoContainer.appendChild(tomato);

    let speed = Math.random() * 3 + 2;
    let angle = Math.random() * 10 - 5;
    let rotation = 0;

    function fall() {
        let top = parseFloat(tomato.style.top);
        if (top < window.innerHeight) {
            tomato.style.top = top + speed + "px";
            rotation += angle;
            tomato.style.transform = `rotate(${rotation}deg)`;
            requestAnimationFrame(fall);
        } else {
            tomato.remove();
        }
    }
    fall();
}

setInterval(createFallingTomato, 500);

