from flask import Flask, render_template, request, redirect
from ner import Ner_Extractor, extractor
from summarize import upload_summary_model, summarize
from pyaspeller import YandexSpeller
from classification import *

app = Flask(__name__)
device = torch.device('cuda' if torch.cuda.is_available() else
                      ('mps' if torch.backends.mps.is_available() else 'cpu'))
summary_tokenizer, summary_model = upload_summary_model()
speller = YandexSpeller()

large_tokenizer, large_label_model = upload_gpt_large_model(device)
small_tokenizer, small_label_model = upload_gpt_small_model(device)

page = 0
entries = [
    {
        'text': """
        Пермь г, +79194692145. В Перми с ноября 2021 года не работает социальное такси. Каким образом можно получить льготу по проезду в такси в соц учреждения инвалиду 2гр.пррезд в общественном транспорте не возможен. Да и проездного льготного не представляется
        """,
    },
    {
        'text': """
        Добрый вечер, помогите пожалуйста в решении проблемы. Улица Стахановская,49-управляющая компания Квант никак не реагирует на обращения жильцов общежития. Протекает крыша, в секции творится ужас. Течь переходит в комнаты . Представители УК ранее говорили, что ремонт кровли запланирован на 2021, но ремонт так и не был произведён. Сейчас УК утверждает, что ремонт запланирован на 2022 год…. Секция в аварийном состоянии, рядом с подтекающими местами находится проводка, мы просили отправить электрика, но нашу просьбу так же проигнорировали… фото ниже….в заключении еще хочу сказать, что ремонт кровли уже проводился в 2017 году, но течь снова началась уже в 2018 из-за халатного отношения Управляющей компании. Помогите пожалуйста в решении проблемы
        """
    },
    {
        'text':
        'Доброе утро! Почему не ремонтируется тротуар в г. Пермь по улице Куйбышева за остановкой "Яблочкова" до перекрестка улиц Куйбышева и Лодыгина? Он же был запланирован. К тому же, ремонт этого перекрестка выполнен некачественно- в месте пересечения дорог образовался асфальтовый уступ, в котором скапливается вода.'

    },
    {
        'text': """
        В квитанциях ссылаются на номер договора на услуги ТБ О, не понятно с кем заключали договор и кто его подписал, а оплату с долгами начиная с 2019 года требуют , если договор не подписали собственники как оплачивать , сведения о количестве проживающих вообще не понятно откуда взяты, также не соответствуют действительности, хоть бы сверяли с МФЦ
        """
    }
]


@app.route('/')
def index():
    # Sample data to pass to HTML
    global page
    dropdown_options = {
        1: 'Лысьвенский городской округ',
        2: 'Министерство социального развития ПК',
        3: 'Город Пермь',
        4: 'Министерство здравоохранения',
        5: 'АО ПРО ТКО',
        6: 'Министерство образования',
        7: 'ИГЖН ПК',
        8: 'Бардымский муниципальный округ Пермского края',
        9: 'Александровский муниципальный округ Пермского края',
        10: 'Губахинский городской округ'
    }
    themeGroups = [
        'Благоустройство', 'Социальное обслуживание и защита',
        'Общественный транспорт', 'Здравоохранение/Медицина',
        'Мусор/Свалки/ТКО', 'Образование', 'Дороги', 'ЖКХ', 'Коронавирус',
        'Экономика и бизнес', 'Культура', 'Связь и телевидение',
        'Газ и топливо', 'Безопасность', 'Спецпроекты', 'Мобилизация',
        'МФЦ "Мои документы"', 'Физическая культура и спорт', 'Торговля',
        'Строительство и архитектура',
        'Памятники и объекты культурного наследия', 'Экология',
        'Государственная собственность', 'Роспотребнадзор',
        'Погребение и похоронное дело', 'Электроснабжение'
    ]

    streets = 1
    organizations = 1

    ### NER
    print(entries[page]['text'])
    ner_list = extractor.get_entities(entries[page]['text'])
    print(ner_list)
    ner_dict = {
        'FACILITY': [],
        'ORGANIZATION': [],
        'DATE': [],
        'NUMBER': [],
    }
    for i in ner_list:
        if i[0] in ('FACILITY', 'ORGANIZATION', 'DATE', 'NUMBER'):
            l = ner_dict[i[0]]
            l.append(entries[page]['text'][i[1]:i[2]])
            ner_dict.update({i[0]: l})
    print(ner_dict)

    ### ThemeGroup
    text_to_predict = entries[page]['text']
    defaultThemeGroup, themGroupProba = predict_class(text_to_predict, large_tokenizer, large_label_model,
                                                      get_large_class(), device)
    themGroupProba = probability_to_percent(themGroupProba)


    themes = map_label(defaultThemeGroup, map_dict)
    ### Theme
    text_to_predict = defaultThemeGroup + ': ' + text_to_predict
    defaultTheme, themeProba = predict_class(text_to_predict, small_tokenizer, small_label_model, get_small_class(),
                                             device)
    themeProba = probability_to_percent(themeProba)

    ### Summary
    summary = correct_summary(speller, summarize(entries[page]['text'], summary_tokenizer, summary_model))

    return render_template('index.html', entries=entries, streets=streets, organizations=organizations, page=page,
                           dropdown_options=dropdown_options, ner_dict=ner_dict, themeGroups=themeGroups,
                           defaultThemeGroup=defaultThemeGroup, themes=themes, defaultTheme=defaultTheme,
                           summary=summary, themeProba=themeProba, themGroupProba=themGroupProba)


@app.route('/change-page', methods=['POST'])
def change_page():
    global page
    if request.form.get('buttonClicked') == 'true':
        if page < 3:
            page += 1
    return redirect('/')


def probability_to_percent(num):
    return str(round(num * 100, 2)) + '%'


def correct_summary(speller, text):
    return speller.spelled(text)


def map_label(big_label, map_dict):
    return map_dict[big_label]


if __name__ == '__main__':
    map_dict = {'Благоустройство': ['★ Ямы во дворах',
                                    'Предложение по благоустройству',
                                    '★ Нарушение правил уборки от снега и наледи внутридворового проезда, тротуара, площади',
                                    'Борщевик Сосновского',
                                    'Парки и зоны отдыха',
                                    'Уборка территорий',
                                    'Благоустройство общественного пространства (парк, сквер, пешеходная зона, бульвар, набережная, центральная улица или площадь)',
                                    '★ Ненадлежащее содержание зеленых насаждений (газонов)/деревьев и кустарников',
                                    'Вырубка деревьев, кустарников',
                                    '★ Неисправные фонари освещения',
                                    '★ Открытые канализационные люки',
                                    'Отсутствие фонарей освещения',
                                    'Разрушение тротуаров и пешеходных дорожек',
                                    'Отсутствие детских площадок',
                                    '★ Нарушение правил уборки от снега и наледи территории парка и сквера',
                                    '★ Отсутствие урн, лавочек в общественных местах и дворовой территории',
                                    'Нарушение правил проведения земляных работ',
                                    '★ Нарушение правил уборки и вывоза порубочных остатков',
                                    'Обустройство асфальтового покрытия парковки, внутридворового проезда, тротуара, пешеходной дорожки, въезда во двор',
                                    'Благоустройство придомовых территорий',
                                    '★ Нарушение правил уборки и вывоза загрязненного снега и наледи на газоне',
                                    '★ Ненадлежащее состояние игровых элементов на детской или спортивной площадке',
                                    '★ Подтопление территории',
                                    '★ Нарушение правил уборки внутридворового проезда, пешеходной дорожки',
                                    'Ненадлежащее состояние фасадов нежилых зданий, объектов и ограждений',
                                    'Отсутствие общественных туалетов',
                                    'Установка ограждений, препятствующих въезду на тротуар, газон на дворовой территории МКД',
                                    'Самовольная установка ограждений на территории общего пользования',
                                    '★ Нарушение правил уборки от снега и наледи детской игровой и спортивной площадки',
                                    '★ Парковка на газонах'],
                'Социальное обслуживание и защита': ['Оказание гос. соц. помощи',
                                                     'Дети и многодетные семьи',
                                                     'Задержка выплат гражданам',
                                                     'Аварийное жилье/переселение',
                                                     'Создание доступной среды для инвалидов',
                                                     'Социальные учреждения',
                                                     'Занятость и трудоустройство',
                                                     'Инвалиды',
                                                     'Пенсионеры и ветераны',
                                                     'Улучшение жилищных условий',
                                                     'Волонтерство',
                                                     'Соц.обслуживание прочее',
                                                     'Матери-одиночки, подростки'],
                'Общественный транспорт': ['Содержание остановок',
                                           'Пешеходные переходы и жд переезды',
                                           'Неудовлетворительные условия проезда в транспорте на действующем маршруте',
                                           'Некорректное поведение водительского состава',
                                           'Льготы на проезд и тарифы',
                                           'График движения общественного транспорта',
                                           'Добавить новый маршрут',
                                           'Отсутствие остановочных пунктов',
                                           'Проблемы с социальными картами или проездными документами',
                                           'Изменение класса и количества автобусов',
                                           'Изменить или отменить маршрут'],
                'Здравоохранение/Медицина': ['Технические проблемы с записью на прием к врачу',
                                             'Диспансеризация',
                                             '★ Просьбы о лечении',
                                             '★ Оказание медицинской помощи не в полном объеме/отказ в оказании медицинской помощи',
                                             'Содержание больниц',
                                             '★ Питание в медицинских учреждениях',
                                             'Нехватка или сокращение врачей и медицинских учреждений',
                                             'Профильный осмотр',
                                             'Очередь',
                                             'Отсутствие лекарств в аптеках',
                                             'Ошибки врачей, халатность',
                                             '★ Скорая помощь',
                                             'Льготные лекарства',
                                             'Вакцинация',
                                             'Хамство медицинских работников',
                                             'Отсутствие лекарств в стационарах',
                                             'Низкая заработная плата врачей',
                                             'Нехватка материально-технического обеспечения',
                                             'Социальная поддержка медперсонала',
                                             'Отсутствие аптек',
                                             'Предложения по созданию лечебных центров',
                                             'Здравоохранение прочее'],
                'Мусор/Свалки/ТКО': ['Плата за вывоз ТКО',
                                     '★ Уборка/Вывоз мусора',
                                     '★ Отсутствие контейнерной площадки/Проезд к контейнерной площадке',
                                     'Проблемы с контейнерами',
                                     'Строительство объектов по обращению с отходами',
                                     'Раздельная сортировка отходов',
                                     'Выброс мусора нарушителем',
                                     '★ Стихийные свалки в городе/в парках/в лесу'],
                'Образование': ['Образовательный процесс',
                                'Детские оздоровительные лагеря',
                                'Безопасность образовательного процесса',
                                'Зарплата учителей',
                                'Дополнительное образование',
                                'Дистанционное образование',
                                'Общее впечатление',
                                'Строительство школ, детских садов',
                                'Нехватка мест в школах',
                                'Содержание гос. образовательных организаций',
                                'ВУЗы и ССУЗы',
                                'Питание',
                                'ЕГЭ, ОГЭ',
                                'Выплаты стипендий',
                                'Проблемы с отоплением детских садов и школ',
                                'Социальная поддержка учителей',
                                'Кадровые перестановки',
                                'Устройство в ДОУ'],
                'Дороги': [
                    '★ Нарушение правил очистки дорог от снега и наледи/Обращения о необходимости очистить тротуар от снега и наледи',
                    'Подтопление автомобильных дорог',
                    'Необходима установка и замена дорожных ограждений',
                    'Предложить установку нового лежачего полицейского (ИДН)',
                    'Ремонт/строительство мостов',
                    'Организация парковок',
                    'Содержание, ремонт и обустройство тротуаров',
                    'Ямы и выбоины на дороге',
                    'Строительство или реконструкция дорог',
                    'Ремонт дороги',
                    '★ Некачественно нанесенная разметка на проезжей части',
                    'Ливневые канализации (строительство и реконструкция)',
                    'Освещение неисправно или отсутствует',
                    'Организация переходов, светофоров/Изменить организацию движения',
                    'Работа светофора (установка, изменение режима работы, оборудование кнопкой вызова)',
                    '★ Несоблюдение правил уборки проезжей части',
                    'Содержание дорожных знаков/Установка новых дорожных знаков, с внесением в схему дислокации, замена старых знаков на новые',
                    'Нарушение технологии и (или) сроков производства работ',
                    'Пробки',
                    'Предложение дороги в план ремонта',
                    'Несанкционированное ограничение движения, помехи движению, захват земли в полосе отвода автодорог',
                    'Некачественно выполненный ремонт дорог'],
                'ЖКХ': ['Жалобы на управляющие компании',
                        'Плата за ЖКУ и работа ЕИРЦ',
                        'Отсутствие холодной воды',
                        'Завышение платы за коммунальные услуги',
                        'Ненадлежащее качество или отсутствие отопления',
                        'Ненадлежащая уборка подъездов и лифтов',
                        'Отсутствие горячей воды',
                        'Некачественный капитальный ремонт',
                        'Сборы за капитальный ремонт',
                        'Дезинфекция МКД',
                        '★ Затопление подъездов, подвальных помещений',
                        'Плохое качество воды',
                        '★ Наледь и сосульки на кровле',
                        'Низкая температура воды/слабое давление',
                        '★ Прорыв трубы/трубопровода',
                        'Ненадлежащее содержание и эксплуатация МКД',
                        'Перепланировка и реконструкция помещений',
                        'Отсутствие электричества',
                        '★ Несанкционированные надписи, рисунки, реклама на фасаде МКД',
                        'Непригодные для проживания жилые помещения',
                        '★ Протечки с кровли (системы водостока)',
                        'Подключение к водоснабжению',
                        'Ремонт подъездов',
                        'Другие проблемы с общедомовой системой водоотведения (канализации)',
                        '★ Засор в общедомовой системе водоотведения (канализации)',
                        'Лифт неисправен или отключен',
                        'Залитие квартиры',
                        'Неисправность выступающих конструкций: балконов, козырьков, эркеров, карнизов входных крылец и т. п.'],
                'Коронавирус': ['Жалобы на врачей',
                                'Тесты на коронавирус',
                                'Доступность вакцин',
                                'Коронавирус',
                                'Порядок и пункты вакцинации',
                                'Сертификаты и QR-коды',
                                'Проблемы в работе горячих линий',
                                'Коронавирусные ограничения',
                                'Самоизоляция и карантин'],
                'Экономика и бизнес': ['Трудоустройство', 'Цены и ценообразование'],
                'Культура': ['Учреждения культуры', 'Культурно-досуговые мероприятия'],
                'Связь и телевидение': ['★ Информационно-техническая поддержка'],
                'Газ и топливо': ['Восстановление газоснабжения',
                                  'Запрос на газификацию и её условия',
                                  'Сроки газификации',
                                  'Стоимость, оплата и возврат средств на газификацию'],
                'Безопасность': ['Безопасность общественных пространств',
                                 'Отлов безнадзорных собак и кошек',
                                 'Беженцы'],
                'Спецпроекты': ['Спецпроекты'],
                'Мобилизация': ['Поддержка семей мобилизованных',
                                'Зарплата, компенсации, поощрения, выплаты'],
                'МФЦ "Мои документы"': ['Государственные услуги', 'МФЦ "Мои документы"'],
                'Физическая культура и спорт': ['Строительство спортивной инфраструктуры',
                                                'Ремонт спортивных учреждений',
                                                'Спортивные мероприятия'],
                'Торговля': ['★ Нестационарная торговля (киоски, павильоны, сезонная торговля)'],
                'Строительство и архитектура': ['Состояние зданий учреждений и организаций',
                                                'Строительство социальных объектов',
                                                'Строительство зданий',
                                                'Архитектура города'],
                'Памятники и объекты культурного наследия': ['Памятники и объекты культурного наследия'],
                'Экология': ['Выбросы вредных веществ в атмосферу/загрязнение воздуха',
                             'Выбросы вредных веществ в водоёмы/загрязнение водоёмов'],
                'Государственная собственность': ['Региональное имущество'],
                'Роспотребнадзор': ['Санитарно-эпидемиологическое благополучие',
                                    'Обработка и уничтожение грызунов (дератизация)'],
                'Погребение и похоронное дело': ['Погребение и похоронное дело'],
                'Электроснабжение': ['Качество электроснабжения', '★ Повреждение опор ЛЭП']}

    app.run(host='0.0.0.0', port=5000)
    #app.run()
