class Type:
    def __init__(self, name):
        self.name = name

    def show_info(self):
        print(f"Тип: {self.name}")


class Class(Type):
    def __init__(self, name, parent=None):
        super().__init__(name)
        self.parent = parent

    def show_tree(self):
        if self.parent:
            self.parent.show_info()
        self.show_info()


class Order(Class):
    def __init__(self, name, parent=None):
        super().__init__(name, parent)


class Family(Order):
    def __init__(self, name, parent=None):
        super().__init__(name, parent)


class Genus(Family):
    def __init__(self, name, parent=None):
        super().__init__(name, parent)


class Species(Genus):
    def __init__(self, name, breed="", color="", weight=0, parent=None):
        super().__init__(name, parent)
        self.breed = breed
        self.color = color
        self.weight = weight

    def show_info(self):
        print(f"Вид: {self.name}")
        print(f"  Порода: {self.breed}")
        print(f"  Цвет: {self.color}")
        print(f"  Вес: {self.weight} кг")

    def show_tree(self):
        # Для Species показываем всю цепочку
        chain = []
        current = self

        # Собираем иерархию
        while current:
            if hasattr(current, '__class__'):
                class_name = current.__class__.__name__
                if hasattr(current, 'name'):
                    chain.append(f"{class_name}: {current.name}")
            current = getattr(current, 'parent', None)

        # Выводим от Type к Species
        for item in reversed(chain):
            print(item)

        # Дополнительная информация
        print(f"  Порода: {self.breed}")
        print(f"  Цвет: {self.color}")
        print(f"  Вес: {self.weight} кг")


class Farm:
    def __init__(self):
        # Создаем иерархию
        self.animal_type = Type("Хордовые")
        self.mammal_class = Class("Млекопитающие", self.animal_type)
        self.artiodactyl_order = Order("Парнокопытные", self.mammal_class)
        self.bovid_family = Family("Полорогие", self.artiodactyl_order)
        self.cattle_genus = Genus("Быки", self.bovid_family)

        # Создаем животных
        self.animals = {
            "Бурёнка": Species("Домашняя корова", "Голштинская", "Чёрно-белая", 600, self.cattle_genus),
        }

    def show_animal_info(self, name):
        if name in self.animals:
            print(f"\n=== Информация о {name} ===")
            self.animals[name].show_tree()
            print("-" * 30)
        else:
            print(f"Животное '{name}' не найдено!")