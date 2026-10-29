"""Create/reconcile only the dedicated Spark issue project using local gh."""
import json
from triage import ROOT, REPO, GROUPS, DESCRIPTIONS, api, graphql

TITLE = 'Spark-X2.6 | Issue Triage & Delivery'
STATUS = ['Triage', 'Ready', 'In progress', 'Blocked', 'In review', 'Done']
PALETTE = ['GRAY', 'BLUE', 'YELLOW', 'RED', 'PURPLE', 'GREEN']
OPTION_COLORS = {
    'priority': ['RED', 'ORANGE', 'YELLOW', 'GRAY'],
    'effort': ['BLUE', 'PURPLE', 'ORANGE', 'GRAY'],
    'risk': ['GREEN', 'YELLOW', 'RED', 'GRAY'],
    'triage': ['GRAY', 'PURPLE', 'YELLOW', 'GREEN', 'GRAY'],
    'area': ['BLUE', 'PURPLE', 'YELLOW', 'GREEN', 'PINK', 'ORANGE', 'GRAY'],
}
PROJECT_QUERY = '''query($id:ID!){node(id:$id){... on ProjectV2{id number url title
  fields(first:50){nodes{... on ProjectV2Field{id name} ... on ProjectV2SingleSelectField{id name options{id name color description}}}}
  views(first:50){nodes{id name layout filter}}}}}'''


def mutate(name, input_type, result, data):
    return graphql(f'mutation($input:{input_type}!){{{name}(input:$input){{{result}}}}}', input=data)[name]


def main():
    if api('user')['login'] != 'FenjuFu':
        raise RuntimeError('Expected FenjuFu account')
    # Find before creating, so interrupted runs do not create duplicates.
    info = graphql('''query{organization(login:"XHToken"){id projectsV2(first:100){nodes{id title closed url number}}}
                      repository(owner:"XHToken",name:"Spark-X2.6"){id}}''')
    matches = [p for p in info['organization']['projectsV2']['nodes'] if p['title'] == TITLE and not p['closed']]
    if len(matches) > 1:
        raise RuntimeError('Multiple matching projects; choose explicitly before continuing')
    if matches:
        project = matches[0]
    else:
        project = mutate('createProjectV2', 'CreateProjectV2Input', 'projectV2{id number url}',
                         {'ownerId': info['organization']['id'], 'title': TITLE,
                          'repositoryId': info['repository']['id']})['projectV2']
    print(project['url'], flush=True)
    mutate('linkProjectV2ToRepository', 'LinkProjectV2ToRepositoryInput', 'repository{id}',
           {'projectId': project['id'], 'repositoryId': info['repository']['id']})
    readme = '''# Spark-X2.6 Issue Triage & Delivery

统一接收模型使用反馈、量化发布、推理部署、评测复现和社区任务。

## 工作流 / Workflow
Triage 待确认 → Ready 已排期 → In progress 处理中 → In review 待验证 → Done 已完成。
Blocked 表示有明确外部依赖；填写 Assignees 指定负责人。仅有讨论不代表正在开发。

## 分类 / Classification
Area 领域、Priority 优先级、Effort 工作量、Risk 风险、Triage 分流均来自同名 issue 标签。
P0 由维护者人工设置；P1 阻碍基本使用；P2 正常排期；P3 低优先级。
unknown 表示信息不足，不表示低风险。agent-ready 只是低风险候选，仍需审阅与验证。

## 自动化 / Automation
本机 gh 规则分类：新 issue 入板并补齐缺失标签；不覆盖人工分类、不自动关单、不自动指派。
手动拖动 Status 管理进度；关闭 issue 后自动移至 Done。
添加 triage-manual 可暂停该 issue 的分类和同步。
本机在线且 Windows 用户登录时定时运行。可选接入 Spark 或兼容模型接口。
'''
    mutate('updateProjectV2', 'UpdateProjectV2Input', 'projectV2{id}',
           {'projectId': project['id'], 'public': True,
            'shortDescription': 'Issue 分流、优先级与交付跟踪 | Rule-based triage with optional Spark model assistance', 'readme': readme})
    node = graphql(PROJECT_QUERY, id=project['id'])['node']
    fields = {f['name']: f for f in node['fields']['nodes']}
    status = fields['Status']
    existing = {x['name']: x for x in status['options']}
    # Only replace the three empty defaults on a newly created project.
    if list(existing) == ['Todo', 'In Progress', 'Done']:
        count = graphql('query($id:ID!){node(id:$id){... on ProjectV2{items{totalCount}}}}', id=project['id'])['node']['items']['totalCount']
        if count:
            raise RuntimeError('Nonempty project uses default status; refusing to discard values')
        options = [{'name': name, 'color': PALETTE[i], 'description': name} for i, name in enumerate(STATUS)]
        mutate('updateProjectV2Field', 'UpdateProjectV2FieldInput', 'projectV2Field{... on ProjectV2SingleSelectField{id}}',
               {'fieldId': status['id'], 'singleSelectOptions': options})
    elif not set(STATUS).issubset(existing):
        options = list(existing.values()) + [{'name': name, 'color': PALETTE[i], 'description': name}
                                           for i, name in enumerate(STATUS) if name not in existing]
        mutate('updateProjectV2Field', 'UpdateProjectV2FieldInput', 'projectV2Field{... on ProjectV2SingleSelectField{id}}',
               {'fieldId': status['id'], 'singleSelectOptions': options})
    for group, choices in GROUPS.items():
        options = [{'name': name, 'color': OPTION_COLORS[group][i], 'description': DESCRIPTIONS[f'{group}/{name}']}
                   for i, name in enumerate(choices)]
        if group.title() not in fields:
            mutate('createProjectV2Field', 'CreateProjectV2FieldInput', 'projectV2Field{... on ProjectV2SingleSelectField{id}}',
                   {'projectId': project['id'], 'name': group.title(), 'dataType': 'SINGLE_SELECT', 'singleSelectOptions': options})
        else:
            current = fields[group.title()]
            by_name = {o['name']: o for o in current['options']}
            for option in options:
                if option['name'] in by_name:
                    option['id'] = by_name[option['name']]['id']
            options.extend(o for o in current['options'] if o['name'] not in choices)
            mutate('updateProjectV2Field', 'UpdateProjectV2FieldInput', 'projectV2Field{... on ProjectV2SingleSelectField{id}}',
                   {'fieldId': current['id'], 'singleSelectOptions': options})
    node = graphql(PROJECT_QUERY, id=project['id'])['node']
    fields = {f['name']: f for f in node['fields']['nodes']}
    config = {**project, 'fields': {name: {'id': f['id'], 'options': {o['name']: o['id'] for o in f['options']}}
                                  for name, f in fields.items() if 'options' in f}}
    (ROOT / 'project.json').write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding='utf-8')
    views = {v['name']: v for v in node['views']['nodes']}
    visible = [fields[name]['id'] for name in ['Title', 'Assignees', 'Status', 'Priority', 'Area', 'Effort', 'Risk', 'Triage', 'Labels'] if name in fields]
    desired = [
        ('01 Delivery | 交付看板', 'BOARD_LAYOUT', ''),
        ('02 Inbox | 待分流', 'TABLE_LAYOUT', 'is:open status:Triage'),
        ('03 Priority | 优先处理', 'TABLE_LAYOUT', 'is:open label:priority/p0,priority/p1'),
        ('04 Agent ready | 可交给 Agent', 'TABLE_LAYOUT', 'is:open label:triage/agent-ready'),
        ('05 Blocked | 阻塞', 'TABLE_LAYOUT', 'is:open status:Blocked'),
        ('06 Community | 社区活动', 'TABLE_LAYOUT', 'is:open label:area/community'),
        ('07 All issues | 全部', 'TABLE_LAYOUT', ''),
    ]
    for i, (name, layout, filter_text) in enumerate(desired):
        view = views.get(name)
        if view is None and i == 0 and len(views) == 1:
            candidate = next(iter(views.values()))
            if candidate['name'] in ('View 1', 'Table'):
                view = candidate
        if view is None:
            view = mutate('createProjectV2View', 'CreateProjectV2ViewInput', 'projectV2View{id name}',
                          {'projectId': project['id'], 'name': name, 'layout': layout,
                           'configuration': {'visibleFieldIds': visible}})['projectV2View']
        mutate('updateProjectV2View', 'UpdateProjectV2ViewInput', 'projectV2View{id name layout filter}',
               {'viewId': view['id'], 'name': name, 'layout': layout, 'filter': filter_text,
                'configuration': {'visibleFieldIds': visible}})
    print(json.dumps(graphql(PROJECT_QUERY, id=project['id'])['node'], ensure_ascii=False))


if __name__ == '__main__':
    main()
