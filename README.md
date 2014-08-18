Powny Cli
=================

Powny command line tools облегчает взаимодействие с Powny API, а так же позволяет проверять работу правил локально.

Установка
-------
В общем случае, должно быть достаточно выполнить:

`pip install powny-cli`

> Утилита протестированна *только* с python >= 3.3

Рекомендуется устанавливать в `virtualenv`.

*Утилита тянет с собой не мало зависимостей (в основном, для локального выполнения правил), будьте к этому готовы*

Что умеет powny-cli
-------

### Загрузить новые или изменённые правила в Powny

+ Склонируйте репозиторий с правилами:

```bash
$ git clone git@github.example-team.ru:alexanderk/powny-load-test-rules.git
$ cd powny-test-rules
```

+ Внесите необходимые изменения:

```bash
$ vim rules/on_event_bar.py
```

+ Что бы загрузить правила в Powny выполните:

```bash
$ powny-cli rules upload -m "Change rule" --api-url=http://powny-testing.example.net:7887
```

> Эта команда пытается синхронизировать ваши изменения с удалённым репозиторием правил, с которым вы работаете.
> А после загружает правила в powny.

*Output:*

```
INFO:pownycli.client:Upload updated rules to Powny...
INFO:pownycli.uploader:Commit current changes...
INFO:pownycli.uploader:Pull changes from rules server...
INFO:pownycli.uploader:Sync you changes with rules server...
INFO:pownycli.uploader:Upload rules to ssh://git@powny-testing.example.net:2022/var/lib/powny/rules.git...
INFO:requests.packages.urllib3.connectionpool:Starting new HTTP connection (1): powny-testing.example.net
INFO:requests.packages.urllib3.connectionpool:Starting new HTTP connection (1): powny-testing.example.net
INFO:pownycli.pownyapi:Set new head: 2238e6636063b57b541c0f1799596e1617dec489
INFO:pownycli.uploader:You rules uploaded to Powny!
```


### Выполнить правило локально

Пусть, репозиторий с правилами на ходится в директории `./powny-rules` и описание события в  `event.json`.

> Убедитесь, что `event.json` в правильном формате, например:

```bash
$ cat event.json
{"host":"foo", "service":"100", "status":"CRIT", "description":"test"}
````

Что бы выполнить правило запустите:

```bash
$ powny-cli --debug rules -r powny-rules exec -e event.json
```

*Output:*

```bash
DEBUG:raava.handlers:Loading rules from head: ; root: /home/cloud-user/powny-cli-test/powny-rules
DEBUG:raava.handlers:Scanning for rules: rules/on_event_bar.py
DEBUG:raava.handlers:Loaded on_event handler from <module 'rules.on_event_bar' from '/home/cloud-user/powny-cli-test/powny-rules/rules/on_event_bar.py'>
DEBUG:raava.handlers:Scanning for rules: rules/on_event_foo_3.py
DEBUG:raava.handlers:Loaded on_event handler from <module 'rules.on_event_foo_3' from '/home/cloud-user/powny-cli-test/powny-rules/rules/on_event_foo_3.py'>
DEBUG:raava.handlers:Scanning for rules: rules/on_event_foo_2.py
DEBUG:raava.handlers:Loaded on_event handler from <module 'rules.on_event_foo_2' from '/home/cloud-user/powny-cli-test/powny-rules/rules/on_event_foo_2.py'>
DEBUG:raava.handlers:Scanning for rules: rules/on_event_foo.py
DEBUG:raava.handlers:Loaded on_event handler from <module 'rules.on_event_foo' from '/home/cloud-user/powny-cli-test/powny-load-test-rules/rules/on_event_foo.py'>
DEBUG:raava.rules:Applied: 0a8e1c3c-b573-4688-9a67-d9f35d56496e --> rules.on_event_foo_3.on_event
DEBUG:raava.rules:Applied: 0a8e1c3c-b573-4688-9a67-d9f35d56496e --> rules.on_event_foo_2.on_event
DEBUG:raava.rules:Applied: 0a8e1c3c-b573-4688-9a67-d9f35d56496e --> rules.on_event_foo.on_event
DEBUG:raava.rules:Event 0a8e1c3c-b573-4688-9a67-d9f35d56496e/host: not matched with <cmp eq(bar)>; handler: rules.on_event_bar.on_event
INFO:requests.packages.urllib3.connectionpool:Starting new HTTP connection (1): example.com
DEBUG:requests.packages.urllib3.connectionpool:"GET / HTTP/1.1" 200 1270
INFO:requests.packages.urllib3.connectionpool:Starting new HTTP connection (1): example.com
DEBUG:requests.packages.urllib3.connectionpool:"GET / HTTP/1.1" 200 1270
INFO:requests.packages.urllib3.connectionpool:Starting new HTTP connection (1): powny-testing.example.net
DEBUG:requests.packages.urllib3.connectionpool:"GET / HTTP/1.1" 200 226
DEBUG:pownyhelpers.output.via_email:Sending email to: ['alexanderk@example-team.ru']; cc: []; via SMTP None@localhost
INFO:pownyhelpers.output.via_email:Email sent to: ['alexanderk@example-team.ru']; cc: []
```

Если `powny-cli` настроен верно, то вы получите все необходимые уведомления.
 
### Получить информацию о Powny кластере

```bash
$ powny-cli powny --api-url=http://powny-testing.example.net:7887 cluster-info
```

*Output:*

```
INFO:requests.packages.urllib3.connectionpool:Starting new HTTP connection (1): powny-testing.example.net
{'collector': {'96365003-b273-46a5-b4c6-8ee984a91c2a@powny-collector-localship': {'host': {'fqdn': 'powny-collector-localship',
                                                                                         'node': 'powny-collector-localship'},
                                                                                'threads': {'die_after': None,
                                                                                            'respawns': 1,
                                                                                            'workers_limit': 1},
                                                                                'when': '2014-07-29T11:10:55Z'}},
 'splitter': {'0f8ee3be-9148-49fd-bb20-ea3e65b0a590@powny-splitter-localship': {'host': {'fqdn': 'powny-splitter-localship',
                                                                                       'node': 'powny-splitter-localship'},
                                                                              'loader': {'last_commit': '33a72fe756df6834f78bc2916651dfba2896d03f',
                                                                                         'last_head': 'git_33a72fe756df6834f78bc2916651dfba2896d03f',
                                                                                         'rules_dir': '/var/lib/powny/rules'},
                                                                              'threads': {'die_after': None,
                                                                                          'respawns': 1,
                                                                                          'workers_limit': 1},
                                                                              'when': '2014-07-29T11:10:53Z'}},
 'worker': {'d6f2b259-433b-4d60-b205-33b9867a2f65@powny-worker-localship': {'host': {'fqdn': 'powny-worker-localship',
                                                                                   'node': 'powny-worker-localship'},
                                                                          'threads': {'die_after': None,
                                                                                      'respawns': 1,
                                                                                      'workers_limit': 1},
                                                                          'when': '2014-07-29T11:10:55Z'}}}
```


### Получить список активных заданий

```bash
$ powny-cli powny --api-url=http://powny-testing.example.net:7887 job-list
```

### Остановить задачу по UUID

```bash
$ powny-cli powny --api-url=http://powny-testing.example.net:7887 kill-job _JOB_UUID_
```


### Послать событие в powny

Если событие простое (состоит из полей `host`, `service`, `severity`), то описание может быть переданно как аргументы:

```bash
$ powny-cli powny --api-url=http://powny-testing.example.net:7887 send-event http://example.com golem CRIT
```

Так же, событие может быть описано в файле, который задаётся опцией `--file`:

```bash
$ powny-cli powny --api-url=http://powny-testing.example.net:7887 send-event --file event.json
```

*Output:*

```
INFO:pownycli.client:Send event: {'host': 'http://example.com', 'service': 'golem', 'severity': 'CRIT'}
INFO:requests.packages.urllib3.connectionpool:Starting new HTTP connection (1): powny-testing.example.net
INFO:pownycli.pownyapi:New event posted. Job Id: ec975edd-5403-44f1-8997-96d3caa8f82d
```

О настройке и опциях
---------
При установке с пакетом поставляется конфиг по умолчанию.
Что бы внести изменения в конфигурацию, необходимые опции можно переписать в файле `~/.config/powny-cli/config.yaml`,
или передать опцию `powny-cli --config=my_config.yaml`.

Можно использовать опцию `--debug` для более подробного вывода. По умолчанию, уровень `INFO`.

Опции, предназначенные для файлов, могут быть выставленны в `-`, в таком случае, вместо файла будет читаться `stdin`.

Например:

```bash
cat event.json |  powny-cli powny --api-url=http://powny-testing.example.net:7887 send-event --file -
```

Опция `--api-url` может быть задана в переменной окружения `powny_API_URL` или определёна в конфиге
 (например, `powny_api_url: http://localhost:7887/api`).
