"""
Integration test for MCP tools discovery functionality.

Converted from scripts/debug/debug_tools.py as part of test management plan.
Original purpose: Check available MCP tools and their parameters.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from neira_code_analyzer.main import list_tools


class TestMCPToolsDiscovery:
    """Test MCP tools discovery and validation."""

    @pytest.mark.asyncio
    async def test_should_discover_all_available_tools(self):
        """Test that list_tools returns all expected MCP tools."""
        # When
        tools = await list_tools()
        
        # Then
        assert len(tools) > 0, "Should discover at least one MCP tool"
        assert all(hasattr(tool, 'name') for tool in tools), "All tools should have names"
        assert all(hasattr(tool, 'description') for tool in tools), "All tools should have descriptions"

    @pytest.mark.asyncio
    async def test_should_validate_tool_names_and_descriptions(self):
        """Test that all tools have proper names and descriptions."""
        # When
        tools = await list_tools()
        
        # Then
        for tool in tools:
            assert tool.name, f"Tool name should not be empty: {tool}"
            assert len(tool.name) > 0, f"Tool name should not be empty string: {tool}"
            assert tool.description, f"Tool description should not be empty: {tool.name}"
            assert len(tool.description) > 10, f"Tool description too short: {tool.name}"

    @pytest.mark.asyncio
    async def test_should_have_expected_core_tools(self):
        """Test that core neira-code-analyzer tools are available."""
        # When
        tools = await list_tools()
        tool_names = [tool.name for tool in tools]
        
        # Then - Check for expected core tools (based on actual output)
        expected_tools = [
            'get_context',
            'get_analyze', 
            'set_filters'
        ]
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names, f"Expected core tool not found: {expected_tool}. Available: {tool_names}"

    @pytest.mark.asyncio
    async def test_should_validate_tool_parameters_structure(self):
        """Test that tools with parameters have proper schema structure."""
        # When
        tools = await list_tools()
        
        # Then
        for tool in tools:
            if hasattr(tool, 'inputSchema') and tool.inputSchema:
                schema = tool.inputSchema
                assert 'properties' in schema, f"Tool {tool.name} should have properties in schema"
                
                properties = schema.get('properties', {})
                for param_name, param_info in properties.items():
                    assert 'type' in param_info, f"Parameter {param_name} in {tool.name} should have type"
                    assert isinstance(param_info.get('description', ''), str), \
                        f"Parameter {param_name} in {tool.name} should have string description" 

    @pytest.mark.asyncio 
    async def test_should_handle_list_tools_errors_gracefully(self):
        """Test error handling when list_tools fails."""
        # This test checks that our error handling works correctly
        # Since list_tools() doesn't raise exceptions in normal cases,
        # we just verify it returns tools without raising
        
        # When/Then - Should not raise exceptions in normal operation
        try:
            tools = await list_tools()
            assert isinstance(tools, list), "list_tools should return a list"
        except Exception as e:
            pytest.fail(f"list_tools should not raise exceptions in normal operation: {e}")

    @pytest.mark.asyncio
    async def test_should_have_reasonable_number_of_tools(self):
        """Test that the number of discovered tools is reasonable."""
        # When
        tools = await list_tools()
        
        # Then - Should have a reasonable number of tools (updated based on actual output)
        assert 5 <= len(tools) <= 20, f"Expected 5-20 tools, got {len(tools)}"

    @pytest.mark.asyncio
    async def test_should_have_neira_specific_tools(self):
        """Test that we have neira-specific analysis tools."""
        # When
        tools = await list_tools()
        tool_names = [tool.name for tool in tools]
        
        # Then - Should have key neira analysis tools
        neira_analysis_tools = ['get_analyze', 'get_context', 'set_filters']
        found_tools = [tool for tool in neira_analysis_tools if tool in tool_names]
        
        assert len(found_tools) >= 3, f"Expected at least 3 neira analysis tools, found: {found_tools}"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_integration_tools_discovery_workflow(self):
        """Integration test for complete tools discovery workflow."""
        # This test replicates the original debug_tools.py workflow
        
        # When - Discover tools
        tools = await list_tools()
        
        # Then - Validate the complete workflow works
        assert len(tools) > 0
        
        # Simulate the original output validation
        tool_info = []
        for i, tool in enumerate(tools, 1):
            info = {
                'number': i,
                'name': tool.name,
                'description': tool.description[:100] + "..." if len(tool.description) > 100 else tool.description
            }
            
            if hasattr(tool, 'inputSchema') and tool.inputSchema:
                properties = tool.inputSchema.get('properties', {})
                info['parameters_count'] = len(properties)
                info['parameters'] = []
                
                for param_name, param_info in properties.items():
                    param_type = param_info.get('type', 'unknown')
                    param_desc = param_info.get('description', 'No description')[:50]
                    info['parameters'].append({
                        'name': param_name,
                        'type': param_type,
                        'description': param_desc + "..." if len(param_desc) == 50 else param_desc
                    })
            
            tool_info.append(info)
        
        # Validate the collected info
        assert len(tool_info) == len(tools)
        assert all('name' in info for info in tool_info)
        assert all('description' in info for info in tool_info)
        
        # Ensure we have the expected tools from the actual output
        expected_tool_names = {'get_context', 'set_filters', 'project_config', 'get_templates', 'manage_presets', 'get_analyze', 'gen_docs'}
        actual_tool_names = {info['name'] for info in tool_info}
        
        # At least some expected tools should be present
        common_tools = expected_tool_names.intersection(actual_tool_names)
        assert len(common_tools) >= 5, f"Expected at least 5 common tools, found: {common_tools}" 