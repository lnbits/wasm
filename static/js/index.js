window.app = Vue.createApp({
  el: '#vue',
  mixins: [window.windowMixin],
  data() {
    return {
      form: {
        timeout_seconds: 3.0,
        max_module_bytes: 1000000,
        max_db_ops_per_min: 120,
        max_kv_bytes: 10000000
      }
    }
  },
  methods: {
    async load() {
      try {
        const {data} = await LNbits.api.request('GET', '/wasm/api/v1/settings')
        this.form = {...this.form, ...data}
      } catch (err) {
        LNbits.utils.notifyApiError(err)
      }
    },
    async save() {
      try {
        await LNbits.api.request('PUT', '/wasm/api/v1/settings', null, this.form)
        Quasar.Notify.create({type: 'positive', message: 'Settings saved'})
      } catch (err) {
        LNbits.utils.notifyApiError(err)
      }
    }
  },
  created() {
    this.load()
  }
})
