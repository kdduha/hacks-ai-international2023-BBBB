# hacks-ai-international2023-BBBB
<div id="badges">
    <a href="https://www.python.org">
        <img src="https://img.shields.io/badge/python-6a6a6a?style=flat&logo=python&logoColor=white" alt="python badge"/>
    </a>
    <a href="https://flask.palletsprojects.com/en/latest/">
        <img src="https://img.shields.io/badge/flask-42aaff?style=flat&logo=flask&logoColor=white" alt="flask badge"/>
    </a>
    <a href="https://scikit-learn.org">
        <img src="https://img.shields.io/badge/sklearn-597b9a?style=flat&logo=sklearn&logoColor=white" alt="sklearn badge"/>
    </a>
    <a href="https://huggingface.co/docs/transformers/index">
        <img src="https://img.shields.io/badge/transformers-ffcf48?style=flat&logo=transformers&logoColor=white" alt="transformers badge"/>
    </a>
    <a href="https://pytorch.org/">
        <img src="https://img.shields.io/badge/pytorch-CB2C31?style=flat&logo=pytorch&logoColor=white" alt="pytorch badge"/>
    </a>
    <a href="https://deep-translator.readthedocs.io/en/stable/README.html">
        <img src="https://img.shields.io/badge/deeptranslator-c27ba0?style=flat&logo=deeptranslator&logoColor=white" alt="deeptranslator badge"/>
    </a>
</div>

___

**Постановка задачи**: автоматизация процесса обработки модераторами обращений в различные гос.учреждения за счет автоматической `классификации текстов` по обобщенным *(25 классов)* и более узким конкретным *(195 классов)* темам, а также вспомогательное `выделение именновых сущностей` внутри обращений *(дата, адрес, номер телефона, организация)* и `суммаризация текстов` *(выжимка из короткого описания заявлений)* + интеграция решений в `первичный веб-MVP` *(минимально жизнеспособный продукт)*

Уникальность решения состоит в том, что оно **нацелено не на полную автоматизацию** труда модераторов, что привело бы к некоторому критически важному ошибок классификации, а **на помощь и оптимизацию сил сотрудников**, которые уже на основе полученных из обращений данных принимают свои решения по их дальнейшей обработке

- Screencast веб-сервиса: [here]()

**Технический ход решения**:
- решение проблемы дисбаланса классов за счет аугментации текстовых данных
  - аугментация через 'deep-translator' редко встречающихся классов *(дополнительно реализовали возможность аугментации через `augmentex` от [SberDevices](https://github.com/ai-forever/augmentex?ysclid=lpcqt7gyks801496770), но в итоговом варианте не использовали)*
  - аугментация всего датасета через саммайризинг с помощью NER-модели `IlyaGusev/rut5_base_sum_gazeta` (для 20k строк использовали мощности Yandex DataSphere), но очищенных от ошибок и мусора данных через `re` и `JamSpell`
  <p> </p>

- классификация обращений по их общим и узким темам
  - в первом случае на обычном и аугментированном датасете дообучили GPT-модель `ai-forever/rugpt3small_based_on_gpt2`, сделав из нее классификатор 
  - во втором случае дообучили такую же модель `ai-forever/rugpt3small_based_on_gpt2`, но в качестве данных подавали конкатенированные строки вида `'<общая тема>: <обращение>'`
  - в итоговом пайплайне сначала по обращению предсказываем общую тему, а потом по этому классу и обращению с помощью второй модели предсказываем узкую тему
  - в первом и во втором пункте попробовали сделать то же самое, но с BERT-моделью `cointegrated/rubert-tiny2` *(ее не включили в MVP)*
  - модели сохранены в папке [`models`](https://drive.google.com/drive/folders/1k9gxIuB-eFLvLA1ISsqFlCT8uXwzl2VU?usp=sharing) в формате `modelname_modeltask_f1valscore` *(`pt` расширение или папка с сэйвпоинтами)*
  <p> </p>

- выделение NER
    - использовали дообученную NER-модель `surdan/LaBSE_ner_nerel`
    - модифицировали output модели, оставив часть именнованных сущностей и объединив соседние одинаковые сущности *(модель могла ошибаться, выделяя подстроки одной строки одной сущностью, вместо выделения всей строки одной сущностью)*
<p> </p>

- обернули все в web-интерфейс на `flask`
    - есть потенциальная возможность выбора профиля оператора
    - есть возможность расширить приложение до взаимодействия с СУБД *(пока данные подгружаются из массива)*
    - к каждому обращению выводится его summary *(краткий пересказ)*
    - к каждому обращению выводится список NER *(дата, адрес, номер телефона, организация)*
    - к каждому обращению выводятся классы по общим и узким темам *(модератор их может исправлять)* с вероятностью в прогнозе
    - все лежит в папке `app` (кроме моделей, которые на google-диске)
    - requirements всего репозитория находится в папке приложения
    - docker-файл лежит в папке
