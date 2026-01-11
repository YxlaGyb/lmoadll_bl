# -*- coding: utf-8 -*-
# lmoadll_bl platform
#
# @copyright  Copyright (c) 2025 lmoadll_bl team
# @license  GNU General Public License 3.0
"""
插件系统核心模块

提供插件加载、管理、事件分发等功能, 支持动态扩展CMS功能
"""
import os
import importlib
import importlib.util
import inspect
from typing import Dict, List, Any, Callable, Optional, Tuple
from abc import ABC, abstractmethod
import logging


class PluginBase(ABC):
    """插件基类"""
    
    def __init__(self):
        self.name = self.__class__.__name__
        self.version = "1.0.0"
        self.description = ""
        self.author = ""
        

    @abstractmethod
    def register(self) -> Dict[str, Any]:
        """注册插件功能
        
        Returns:
            Dict[str, Any]: 插件注册信息
        """
        pass
    

    def on_enable(self):
        """插件启用时的回调"""
        pass
        

    def on_disable(self):
        """插件禁用时的回调"""
        pass


class PluginManager:
    """插件管理器"""
    def __init__(self, plugin_dir: str):
        self.plugin_dir = plugin_dir
        self.plugins: Dict[str, PluginBase] = {}
        self.hooks: Dict[str, List[Tuple[str, Callable]]] = {}
        self.api_routes: List[Tuple[str, Callable]] = []
        self.logger = logging.getLogger(__name__)


    def load_plugins(self) -> bool:
        """加载所有插件
        
        Returns:
            bool: 是否加载成功
        """
        try:
            # 扫描插件目录, 只加载包含__init__.py的文件夹插件
            if not os.path.exists(self.plugin_dir):
                os.makedirs(self.plugin_dir)
                self.logger.info(f"创建插件目录: {self.plugin_dir}")
                return True
                
            for item in os.listdir(self.plugin_dir):
                plugin_path = os.path.join(self.plugin_dir, item)
                
                if os.path.isdir(plugin_path):
                    init_file = os.path.join(plugin_path, "__init__.py")
                    if os.path.exists(init_file):
                        if self.load_plugin_from_folder(item, plugin_path):
                            self.logger.info(f"成功加载插件: {item}")
                        else:
                            self.logger.error(f"加载插件失败: {item}")
            return True
        except Exception as e:
            self.logger.error(f"加载插件时发生错误: {e}")
            return False

    
    def load_plugin_from_folder(self, plugin_name: str, plugin_path: str) -> bool:
        """从插件文件夹加载插件
        
        Args:
            plugin_name: 插件名称
            plugin_path: 插件文件夹路径
            
        Returns:
            bool: 是否加载成功
        """
        try:
            # 动态导入插件模块
            spec = importlib.util.spec_from_file_location(plugin_name, os.path.join(plugin_path, "__init__.py"))
            if spec is None:
                self.logger.error(f"无法为插件 {plugin_name} 创建 ModuleSpec, 跳过该插件")
                return False
            module = importlib.util.module_from_spec(spec)
            
            # 设置模块的__package__属性，确保相对导入正常工作
            module.__package__ = f"contents.plugin.{plugin_name}"
            
            # 检查 loader 是否存在
            if spec.loader is None:
                self.logger.error(f"插件 {plugin_name} 的 ModuleSpec 没有 loader, 跳过该插件")
                return False
            
            spec.loader.exec_module(module)
            
            return self._instantiate_plugins(module, plugin_name)
        except Exception as e:
            self.logger.error(f"加载插件 {plugin_name} 失败: {e}")
            return False
    

    def _instantiate_plugins(self, module, plugin_name: str) -> bool:
        """实例化插件类
        
        Args:
            module: 导入的模块
            plugin_name: 插件名称
            
        Returns:
            bool: 是否实例化成功
        """
        try:
            # 查找插件类(继承自PluginBase的类)
            plugin_classes = []
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, PluginBase) and 
                    obj != PluginBase):
                    plugin_classes.append(obj)
            
            if not plugin_classes:
                self.logger.warning(f"插件 {plugin_name} 中没有找到有效的插件类")
                return False
                
            # 实例化插件
            for plugin_class in plugin_classes:
                plugin_instance = plugin_class()
                
                # 从模块级别获取插件信息(优先使用__init__.py中的信息)
                if hasattr(module, 'PLUGIN_INFO'):
                    plugin_info = getattr(module, 'PLUGIN_INFO', {})
                    plugin_instance.name = plugin_info.get('name', plugin_instance.name)
                    plugin_instance.version = plugin_info.get('version', plugin_instance.version)
                    plugin_instance.description = plugin_info.get('description', plugin_instance.description)
                    plugin_instance.author = plugin_info.get('author', plugin_instance.author)
                
                # 注册插件
                registration = plugin_instance.register()
                if not isinstance(registration, dict):
                    self.logger.error(f"插件 {plugin_name} 注册信息格式错误")
                    continue
                    
                # 存储插件实例
                self.plugins[plugin_instance.name] = plugin_instance
                
                # 注册钩子
                if 'hooks' in registration:
                    self._register_hooks(plugin_instance.name, registration['hooks'])
                
                # 注册API路由
                if 'api_routes' in registration:
                    self._register_api_routes(plugin_instance.name, registration['api_routes'])
                
                # 调用启用回调
                plugin_instance.on_enable()
                
            return True
            
        except Exception as e:
            self.logger.error(f"加载插件 {plugin_name} 失败: {e}")
            return False
    

    def _register_hooks(self, plugin_name: str, hooks: Dict[str, Callable]):
        """注册插件钩子
        
        Args:
            plugin_name: 插件名称
            hooks: 钩子字典
        """
        for hook_name, hook_func in hooks.items():
            if hook_name not in self.hooks:
                self.hooks[hook_name] = []
            self.hooks[hook_name].append((plugin_name, hook_func))
            self.logger.debug(f"插件 {plugin_name} 注册钩子: {hook_name}")
    
    def _register_api_routes(self, plugin_name: str, routes_func: Callable):
        """注册插件API路由
        
        Args:
            plugin_name: 插件名称
            routes_func: 路由注册函数
        """
        self.api_routes.append((plugin_name, routes_func))
        self.logger.debug(f"插件 {plugin_name} 注册API路由")
    

    def call_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """调用钩子
        
        Args:
            hook_name: 钩子名称
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            List[Any]: 所有钩子的返回值列表
        """
        results = []
        if hook_name in self.hooks:
            for plugin_name, hook_func in self.hooks[hook_name]:
                try:
                    result = hook_func(*args, **kwargs)
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"调用钩子 {hook_name} 时发生错误: {e}")
        return results
    
    def register_all_api_routes(self, app) -> bool:
        """注册所有插件的API路由
        
        Args:
            app: Quart应用实例
            
        Returns:
            bool: 是否注册成功
        """
        try:
            for plugin_name, routes_func in self.api_routes:
                try:
                    routes_func(app)
                    self.logger.info(f"成功注册插件 {plugin_name} 的API路由")
                except Exception as e:
                    self.logger.error(f"注册插件 {plugin_name} 的API路由失败: {e}")
                    return False
            return True
        except Exception as e:
            self.logger.error(f"注册API路由时发生错误: {e}")
            return False
    

    def get_plugin(self, plugin_name: str) -> Optional[PluginBase]:
        """获取插件实例
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            Optional[PluginBase]: 插件实例或None
        """
        return self.plugins.get(plugin_name)
    

    def get_all_plugins(self) -> Dict[str, PluginBase]:
        """获取所有插件
        
        Returns:
            Dict[str, PluginBase]: 插件字典
        """
        return self.plugins.copy()
    

    def unload_plugin(self, plugin_name: str) -> bool:
        """卸载插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 是否卸载成功
        """
        if plugin_name not in self.plugins:
            return False
            
        try:
            # 调用禁用回调
            self.plugins[plugin_name].on_disable()
            
            # 移除钩子
            for hook_name in list(self.hooks.keys()):
                self.hooks[hook_name] = [
                    (pname, hook_func) for pname, hook_func in self.hooks[hook_name] 
                    if pname != plugin_name
                ]
                if not self.hooks[hook_name]:
                    del self.hooks[hook_name]
            
            # 移除API路由
            self.api_routes = [
                (pname, routes_func) for pname, routes_func in self.api_routes
                if pname != plugin_name
            ]
            
            # 移除插件
            del self.plugins[plugin_name]
            
            self.logger.info(f"成功卸载插件: {plugin_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"卸载插件 {plugin_name} 失败: {e}")
            return False


_plugin_manager: Optional[PluginManager] = None


def init_plugin_system(plugin_dir: str) -> PluginManager:
    """初始化插件系统
    
    Args:
        plugin_dir: 插件目录路径
        
    Returns:
        PluginManager: 插件管理器实例
    """
    global _plugin_manager
    _plugin_manager = PluginManager(plugin_dir)
    return _plugin_manager


def get_plugin_manager() -> PluginManager:
    """获取插件管理器
    
    Returns:
        PluginManager: 插件管理器实例
        
    Raises:
        RuntimeError: 插件系统未初始化
    """
    if _plugin_manager is None:
        raise RuntimeError("插件系统未初始化，请先调用 init_plugin_system()")
    return _plugin_manager


def call_plugin_hook(hook_name: str, *args, **kwargs) -> List[Any]:
    """调用插件钩子(便捷函数)
    
    Args:
        hook_name: 钩子名称
        *args: 位置参数
        **kwargs: 关键字参数
        
    Returns:
        List[Any]: 所有钩子的返回值列表
    """
    return get_plugin_manager().call_hook(hook_name, *args, **kwargs)
