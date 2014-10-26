import os, re
from glob import glob
from urllib.request import urlopen, urlretrieve
from collections import Counter
from time import time
from zipfile import ZipFile
from tkinter import *
from tkinter.ttk import *
from tkinter.messagebox import showinfo

def update_tsv_export(reporthook=None):
    """If export is missing or not current, download the current one. Returns True iff the export was updated."""

    # Is export file missing or older than 10 minutes?
    here = glob('WCA_export*_*.tsv.zip')
    if not here or time() - os.stat(max(here)).st_mtime > 10 * 60:

        # What's the current export on the WCA site?
        base = 'https://www.worldcubeassociation.org/results/misc/'
        try:
            with urlopen(base + 'export.html') as f:
                current = re.search(r'WCA_export\d+_\d+.tsv.zip', str(f.read())).group(0)
        except:
            print('failed looking for the newest export')
            return

        # Download if necessary, otherwise mark local as up-to-date
        if not os.path.isfile(current):
            if not reporthook:
                print('downloading export', current, '...')
            urlretrieve(base + current, current, reporthook)
            for h in here:
                if h != current:
                    os.remove(h)
            return True
        else:
            os.utime(max(here))

def ranking_data():
    """Compute the data which can then be used for display or export."""

    prepare_data()

    # What's currently checked?
    checked = [i for i, v in enumerate(vars) if v.get()]

    # Compute everybody's sum of ranks (of the checked events)
    sums = [(sum(ranks[i] for i in checked), personId)
            for personId, ranks in person_ranks.items()]

    # We'll use this to not show people with only default ranks
    default_sum = sum(default_ranks[i] for i in checked)

    # Build and return the rows to display
    rows = []
    ctr, prev_sum = 0, None
    for sum_, personId in sorted(sums):
        ctr += 1
        pos = '' if sum_ == prev_sum else ctr
        if sum_ == default_sum or type(pos) is int and pos > 100:
            break
        rows.append([pos, person_name[personId], sum_] + person_ranks[personId])
        prev_sum = sum_
    return rows

def show():
    for x in tree.get_children():
        tree.delete(x)
    tree['displaycolumns'] = 'pos cuber sum ' + ' '.join(e for e, v in zip(eventIds, vars) if v.get())
    for i, row in enumerate(ranking_data()):
        tree.insert('', 'end', values=row, tags=('', 'stripe')[i % 2])

def export():
    showinfo(message='Not finished yet, sorry.')
    return
    rows = ranking_data()
    note = 'TODO'
    out = '[SPOILER=Sum of Ranks ("' + 'TODO' + '")]' + note + '\n\n[TABLE="class:grid, align:right"]'
    #out += '[TR][TD][B]' + '[/B][/TD][TD][B]'.join(n.split('[')[0] for n in column_names) + '[/B][/TD][/TR]'
    def td(value):
        #return '[TD' + '=align:left' * (type(value) is str) + ']' + str(value) + '[/TD]'
        return '[TD' + '=align:left' * (type(value) is str) + ']{}[/TD]'.format(value)
    out += '\n'.join('[TR]' + ''.join(td(value) for value in row) + '[/TR]'
                     for row in rows)
    out += '\n[/TABLE][/SPOILER]'
    print(out)

def prepare_data():
    global eventIds, event_name, person_name, person_ranks, default_ranks, eventIdsA, eventIndex

    if 'person_ranks' in globals() and not update_tsv_export():
        return

    print('preparing data ...')
    with ZipFile(max(glob('WCA_export*_*.tsv.zip'))) as zf:

        def load(wanted_table, wanted_columns):
            with zf.open('WCA_export_' + wanted_table + '.tsv') as tf:
                column_names, *rows = [line.split('\t') for line in tf.read().decode().splitlines()]
                columns = []
                for name in wanted_columns.split():
                    i = column_names.index(name)
                    column = [row[i] for row in rows]
                    try:
                        column = list(map(int, column))
                    except:
                        pass
                    columns.append(column)
                return list(zip(*columns))

        event_name = dict(load('Events', 'id cellName'))
        event_rank = dict(load('Events', 'id rank'))
        person_name = dict((id, name) for id, subid, name in load('Persons', 'id subid name') if subid == 1)

        # Get (personId, eventId, rank) triples, appending 'A' to eventIds of averages
        ranks = load('RanksSingle', 'personId eventId worldRank') + \
                [(p, e + 'A', r) for p, e, r in load('RanksAverage', 'personId eventId worldRank')]

        # List of eventIds sorted by rank (and singles before averages)
        eventIds = sorted({r[1] for r in ranks}, key=lambda e: (e.endswith('A'), event_rank[e.strip('A')]))
        eventIndex = {id: i for i, id in enumerate(eventIds)}

        # Compute the default ranks (the "red numbers")
        list_sizes = Counter(r[1] for r in ranks)
        default_ranks = [list_sizes[id] + 1 for id in eventIds]

        # Build person_ranks
        person_ranks = {r[0]: default_ranks[:] for r in ranks}
        for personId, eventId, rank in ranks:
            person_ranks[personId][eventIndex[eventId]] = rank

def make_me_look_good():
    showinfo(message='Not implemented yet, sorry.')

update_tsv_export()
prepare_data()

# The window
root = Tk()
root.title('Sum of WCA Ranks')
root.iconbitmap('icon.ico')

# The checkbuttons & co
Label(root, text='Single').grid(row=0, column=1)
Label(root, text='Average').grid(row=0, column=2)
vars = []
for i, eventId in enumerate(eventIds, 1):
    a = eventId.endswith('A')
    if not a:
        Label(root, text=event_name[eventId]).grid(row=i, column=0)
        bottom = i + 1
    vars.append(IntVar(value=not a))
    Checkbutton(root, variable=vars[-1], command=show).grid(row=1 + eventIndex[eventId.strip('A')], column=1 + a)
def check(value, averages=False):
    for v, eventId in zip(vars, eventIds):
        if eventId.endswith('A') == averages:
            v.set(value)
    show()
Button(root, text='All', width=5, command=lambda: check(1)).grid(row=bottom, column=1)
Button(root, text='None', width=5, command=lambda: check(0)).grid(row=bottom + 1, column=1)
Button(root, text='All', width=5, command=lambda: check(1, True)).grid(row=bottom, column=2)
Button(root, text='None', width=5, command=lambda: check(0, True)).grid(row=bottom + 1, column=2)

# The ranking display
tree = Treeview(root, columns='pos cuber sum ' + ' '.join(eventIds), show='headings')
tree.tag_configure('stripe', background='#DDD')
tree.column('pos', anchor='e', width=35)
tree.heading('pos', text='Pos', anchor='e')
tree.column('cuber', width=150)
tree.heading('cuber', text='Cuber', anchor='w')
tree.column('sum', width=40, anchor='e')
tree.heading('sum', text='Sum', anchor='e')
for eventId in eventIds:
    tree.column(eventId, width=50, anchor='e')
    tree.heading(eventId, text=eventId, anchor='e')
tree.grid(row=0, column=3, rowspan=bottom + 2, columnspan=2, sticky='nswe')
vsb = Scrollbar(root, orient="vertical", command=tree.yview)
vsb.grid(row=0, column=5, rowspan=bottom + 2, sticky='ns')
tree.configure(yscrollcommand=vsb.set)
Button(root, text='Export for speedsolving.com', command=export).grid(row=bottom + 3, column=3)
Button(root, text='Make me look good', command=make_me_look_good).grid(row=bottom + 3, column=4)

# Let's do this!
root.after_idle(show)
root.mainloop()
