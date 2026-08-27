from app import app
from model import db
from model.User import User
from model.Card import Card
from model.Comment import Comment
from model.Tags import Tags
from model.Notification import Notification
from utils.notification import notify_admins
from utils.system import get_config, set_config
import random

app.config['TESTING'] = True

with app.app_context():
    # 1. Create test users
    test_users = [
        {'username': 'zhangsan', 'nickname': '张三', 'email': 'zhangsan@test.com'},
        {'username': 'lisi', 'nickname': '李四', 'email': 'lisi@test.com'},
        {'username': 'wangwu', 'nickname': '王五', 'email': 'wangwu@test.com'},
    ]

    created_users = []
    for u in test_users:
        existing = db.session.execute(db.select(User).where(User.username == u['username'])).scalar()
        if existing:
            created_users.append(existing)
            print('User already exists: %s' % u['username'])
            continue
        new_user = User(number='0', username=u['username'], nickname=u['nickname'], email=u['email'], status=0, roles_id=[2])
        new_user.set_password('123456')
        db.session.add(new_user)
        db.session.flush()
        new_user.number = str(1000000000 + new_user.id)
        created_users.append(new_user)
        print('Created user: %s (%s)' % (u['username'], u['nickname']))

    # Create a pending review user
    pending_existing = db.session.execute(db.select(User).where(User.username == 'pending_user')).scalar()
    if not pending_existing:
        pending_user = User(number='0', username='pending_user', nickname='待审核用户', email='pending@test.com', status=2, roles_id=[2])
        pending_user.set_password('123456')
        db.session.add(pending_user)
        db.session.flush()
        pending_user.number = str(1000000000 + pending_user.id)
        notify_admins('user_pending', '新用户待审核', '用户 pending_user 注册待审核', {'user_id': pending_user.id})
        print('Created pending user: pending_user (status=2)')
    else:
        print('Pending user already exists')

    db.session.commit()

    # 2. Create test cards
    card_contents = [
        '今天天气真好，适合出去散步',
        '图书馆的猫好可爱啊，每天都要去看它',
        '食堂新出的麻辣香锅绝了，推荐大家去尝尝',
        '有没有一起打羽毛球的小伙伴？晚上操场约起来',
        '毕业季真的好舍不得，四年转眼就过去了',
        '考研加油！我们顶峰相见',
        '校园里的银杏叶黄了，好美',
        '求推荐学校附近好吃的外卖',
    ]

    need_review = get_config('siteCardNeedReview') != 'false'
    admin = db.session.execute(db.select(User).where(User.roles_id.contains([0])).limit(1)).scalar()
    if not admin:
        admin = db.session.execute(db.select(User).limit(1)).scalar()

    created_cards = []
    for i, content in enumerate(card_contents):
        author = created_users[i % len(created_users)]
        status = 1 if i < 5 else 0
        card = Card(
            user_id=author.id,
            content=content,
            status=status,
            is_top=0,
            good=random.randint(0, 20),
            views=random.randint(10, 200),
            comments=0,
        )
        db.session.add(card)
        created_cards.append((card, status))
        status_text = 'approved' if status == 1 else 'pending'
        print('Created card (%s): %s' % (status_text, content[:20]))

    # Add pending card notification for admins
    for card, status in created_cards:
        if status == 0:
            db.session.flush()
            notify_admins('card_pending', '新卡片待审核', '用户 %s 发布的卡片待审核' % card.author.display_name, {'card_id': card.id})

    db.session.commit()

    # 3. Create test comments
    comment_contents = [
        '说得好！',
        '同感，+1',
        '哈哈我也看到了',
        '在哪里在哪里？我也想去',
        '加油加油！',
        '太真实了',
        '羡慕了',
        '冲冲冲',
        '我也想加入',
        '下次一起呀',
    ]

    approved_cards = db.session.execute(
        db.select(Card).where(Card.status == 1).limit(5)
    ).scalars().all()

    comment_need_review = get_config('siteCommentNeedReview') != 'false'
    comment_idx = 0
    for card in approved_cards:
        num_comments = random.randint(1, 3)
        for _ in range(num_comments):
            author = created_users[comment_idx % len(created_users)]
            status = 1 if comment_idx < 6 else 0
            comment = Comment(
                aid=1,
                pid=card.id,
                user_id=author.id,
                content=comment_contents[comment_idx % len(comment_contents)],
                status=status,
                is_top=0,
                goods=random.randint(0, 5),
            )
            db.session.add(comment)
            if status == 1:
                card.comments = (card.comments or 0) + 1
            else:
                db.session.flush()
                notify_admins('comment_pending', '新评论待审核', '用户 %s 的评论待审核' % author.display_name, {'card_id': card.id})
            status_text = 'approved' if status == 1 else 'pending'
            print('Created comment (%s) on card #%d: %s' % (status_text, card.id, comment.content))
            comment_idx += 1

    db.session.commit()

    # Summary
    total_users = db.session.execute(db.select(db.func.count(User.id)).where(User.deleted_at.is_(None))).scalar()
    pending_users = db.session.execute(db.select(db.func.count(User.id)).where(User.status == 2, User.deleted_at.is_(None))).scalar()
    total_cards = db.session.execute(db.select(db.func.count(Card.id)).where(Card.deleted_at.is_(None))).scalar()
    pending_cards = db.session.execute(db.select(db.func.count(Card.id)).where(Card.status == 0, Card.deleted_at.is_(None))).scalar()
    total_comments = db.session.execute(db.select(db.func.count(Comment.id)).where(Comment.deleted_at.is_(None))).scalar()
    pending_comments = db.session.execute(db.select(db.func.count(Comment.id)).where(Comment.status == 0, Comment.deleted_at.is_(None))).scalar()
    total_notifs = db.session.execute(db.select(db.func.count(Notification.id))).scalar()

    print()
    print('=== Test Data Summary ===')
    print('Users: %d total, %d pending review' % (total_users, pending_users))
    print('Cards: %d total, %d pending review' % (total_cards, pending_cards))
    print('Comments: %d total, %d pending review' % (total_comments, pending_comments))
    print('Admin notifications: %d' % total_notifs)
