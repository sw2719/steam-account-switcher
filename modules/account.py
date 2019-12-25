from ruamel.yaml import YAML

yaml = YAML()


def acc_getlist():
    with open('accounts.yml', 'r', encoding='utf-8') as acc:
        acc_dict = yaml.load(acc)

    accounts = []
    if acc_dict:
        for x in range(len(acc_dict)):  # to preserve the order
            try:
                cur_dict = acc_dict[x]
                accounts.append(cur_dict['accountname'])
            except KeyError:
                break
    return accounts


def acc_getdict():
    with open('accounts.yml', 'r', encoding='utf-8') as acc:
        acc_dict = yaml.load(acc)

    return acc_dict
