import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ZabbixConfig } from '@/types'
import * as zabbixApi from '@/api/zabbixConfig'

export const useZabbixConfigStore = defineStore('zabbixConfig', () => {
  const configs = ref<ZabbixConfig[]>([])
  const selectedConfigId = ref<string | null>(
    localStorage.getItem('selectedZabbixConfigId')
  )

  const activeConfigs = computed(() => {
    return configs.value.filter((c: ZabbixConfig) => c.is_active)
  })

  async function fetchConfigs() {
    configs.value = await zabbixApi.getAllConfigs()
  }

  function selectConfig(configId: string | null) {
    selectedConfigId.value = configId
    if (configId) {
      localStorage.setItem('selectedZabbixConfigId', configId)
    } else {
      localStorage.removeItem('selectedZabbixConfigId')
    }
  }

  function getSelectedConfig() {
    if (!selectedConfigId.value) return null
    if (selectedConfigId.value === 'unconfigured') return null
    return configs.value.find((c: ZabbixConfig) => c.id === parseInt(selectedConfigId.value!))
  }

  function getSelectedConfigName() {
    if (!selectedConfigId.value) return '请选择配置'
    if (selectedConfigId.value === 'unconfigured') return '未配置'
    const config = getSelectedConfig()
    return config?.name || '请选择配置'
  }

  return {
    configs,
    selectedConfigId,
    activeConfigs,
    fetchConfigs,
    selectConfig,
    getSelectedConfig,
    getSelectedConfigName
  }
})
