"""RBAC 系统初始化"""
from quart import Quart
from magic.service.rbac.permissionService import PermissionService

async def initDefaultRbac(app: Quart):
    """
    初始化默认 RBAC 数据
    
    这个方法创建系统的基础角色和权限。
    建议在系统安装或首次启动时调用。
    
    默认角色:
        - superadmin: 超级管理员，拥有所有权限
        - admin: 管理员，管理大部分功能
        - editor: 编辑者，管理内容
        - user: 普通用户，基本权限
        - visitor: 访客，最小权限
    """
    async with app.app_context():
        permissionsConfig = [
            ('user:read', '查看用户信息', '用户管理'),
            ('user:create', '创建新用户', '用户管理'),
            ('user:edit', '编辑用户信息', '用户管理'),
            ('user:delete', '删除用户', '用户管理'),
            ('post:read', '查看文章', '内容管理'),
            ('post:create', '创建文章', '内容管理'),
            ('post:edit', '编辑文章', '内容管理'),
            ('post:delete', '删除文章', '内容管理'),
            ('post:publish', '发布文章', '内容管理'),
            ('comment:read', '查看评论', '内容管理'),
            ('comment:create', '创建评论', '内容管理'),
            ('comment:delete', '删除评论', '内容管理'),
            ('comment:moderate', '审核评论', '内容管理'),
            ('system:config', '系统配置', '系统管理'),
            ('system:logs', '查看日志', '系统管理'),
            ('system:backup', '数据备份', '系统管理'),
            ('system:plugin', '插件管理', '系统管理'),
        ]
        
        for permName, permDesc, category in permissionsConfig:
            PermissionService.getOrCreatePermission(permName, permDesc, category)
        
        rolePermissions = {
            'superadmin': [
                'user:read', 'user:create', 'user:edit', 'user:delete',
                'post:read', 'post:create', 'post:edit', 'post:delete', 'post:publish',
                'comment:read', 'comment:create', 'comment:delete', 'comment:moderate',
                'system:config', 'system:logs', 'system:backup', 'system:plugin',
            ],
            'admin': [
                'user:read', 'user:create', 'user:edit', 'user:delete',
                'post:read', 'post:create', 'post:edit', 'post:delete', 'post:publish',
                'comment:read', 'comment:create', 'comment:delete', 'comment:moderate',
                'system:logs',
            ],
            'editor': [
                'post:read', 'post:create', 'post:edit', 'post:publish',
                'comment:read', 'comment:create',
            ],
            'user': [
                'post:read',
                'comment:read', 'comment:create',
            ],
            'visitor': [
                'post:read',
            ],
        }
        
        roleDescriptions = {
            'superadmin': '超级管理员，拥有系统所有权限',
            'admin': '管理员，负责系统日常管理',
            'editor': '编辑者，负责内容创作和编辑',
            'user': '普通用户，可阅读内容和发表评论',
            'visitor': '访客，仅可浏览公开内容',
        }
        
        for roleName, perms in rolePermissions.items():
            role = PermissionService.getOrCreateRole(
                roleName, 
                roleDescriptions.get(roleName, '')
            )
            for permName in perms:
                PermissionService.grantPermissionToRole(roleName, permName)
