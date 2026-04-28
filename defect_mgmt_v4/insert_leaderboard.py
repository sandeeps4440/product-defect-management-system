content = open('complaints/views.py').read()
old = '# ── analytics ───────────────────────────────────────────────────────────────'

insert = '''# ── leaderboard helper & views ───────────────────────────────────────────────

def _get_leaderboard():
    return (
        User.objects
        .filter(rewards__isnull=False)
        .select_related('profile')
        .annotate(
            resolved_count=Count('rewards__complaint', distinct=True),
            total_earned=Sum('rewards__amount'),
        )
        .order_by('-resolved_count', '-total_earned')[:20]
    )


@login_required
def leaderboard_view(request):
    profile    = _profile(request.user)
    board      = _get_leaderboard()
    my_rewards = Reward.objects.filter(user=request.user)
    my_count   = my_rewards.count()
    my_earned  = my_rewards.aggregate(t=Sum('amount'))['t'] or 0
    return render(request, 'complaints/leaderboard.html', {
        'profile':       profile,
        'board':         board,
        'my_count':      my_count,
        'my_earned':     my_earned,
        'reward_amount': REWARD_AMOUNT,
    })


'''

assert old in content, 'OLD not found'
open('complaints/views.py', 'w').write(content.replace(old, insert + old, 1))
print('done')
