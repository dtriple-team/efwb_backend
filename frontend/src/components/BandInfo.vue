<template>
  <div>
    <v-card flat height="120" class="primary rounded-0 mx-auto"> </v-card>
    <v-card
      flat
      width="100"
      height="100"
      class="center secondary mt-n13 mx-auto"
      ><v-icon size="85" color="black" class="icon">
        mdi-account-circle
      </v-icon>
    </v-card>
    <v-card flat>
      <v-card-text class="display-1 text-center font-weight-bold">
        {{ band.name }}
      </v-card-text>
    </v-card>
    <v-container fluid>
      <v-list>
        <div class="border-style-top rounded-t-lg">
          <div class="body-2 black--text ml-2 mt-2">생체 데이터</div>
          <v-list-item>
            <v-list-item-content>
              <div class="mx-auto text-center">
                <v-avatar color="thirdly" size="90" class="mb-2">
                  <span class="text-h5 font-weight-bold">80</span>
                </v-avatar>
                <h5>심박수 (BPM)</h5>
              </div>
            </v-list-item-content>
            <v-list-item-content>
              <div class="mx-auto text-center">
                <v-avatar color="thirdly" size="90" class="mb-2">
                  <span class="text-h5 font-weight-bold">80</span>
                </v-avatar>
                <h5>산소포화도 (%)</h5>
              </div>
            </v-list-item-content>
          </v-list-item>
        </div>
        <div flat outlined class="border-style rounded-b-lg">
          <div class="body-2 black--text ml-2 mt-2">밴드 상태</div>
          <v-list-item>
            <v-list-item-content>
              <div class="mx-auto text-center">
                <v-avatar color="thirdly" size="55" class="mb-2">
                  <v-icon color="black">
                    mdi-check-bold
                  </v-icon>
                </v-avatar>
                <h5>착용</h5>
              </div>
            </v-list-item-content>
            <v-list-item-content>
              <div class="mx-auto text-center">
                <v-avatar color="thirdly" size="55" class="mb-2">
                  <span class="text-h5 font-weight-bold">80</span>
                </v-avatar>
                <h5>수신감도</h5>
              </div>
            </v-list-item-content>
            <v-list-item-content>
              <div class="mx-auto text-center">
                <v-avatar color="thirdly" size="55" class="mb-2">
                  <span class="text-h5 font-weight-bold">80</span>
                </v-avatar>
                <h5>배터리</h5>
              </div>
            </v-list-item-content>
            <v-list-item-content>
              <div class="mx-auto text-center">
                <v-avatar color="thirdly" size="55" class="mb-2">
                  <v-icon color="black">mdi-walk</v-icon>
                </v-avatar>
                <h5>활동</h5>
              </div>
            </v-list-item-content>
          </v-list-item>
        </div>
        <div flat class="border-style rounded-lg mt-5">
          <div class="body-2 black--text ml-2 mt-2">활동 이력</div>
          <v-list-item>
            <v-list-item-content>
              <div class="mx-auto text-center">
                <v-avatar color="thirdly" size="55" class="mb-2">
                  <span class="text-h5 font-weight-bold">80</span>
                </v-avatar>
                <h5>걷기</h5>
              </div>
            </v-list-item-content>
            <v-list-item-content>
              <div class="mx-auto text-center">
                <v-avatar color="thirdly" size="55" class="mb-2">
                  <span class="text-h5 font-weight-bold">80</span>
                </v-avatar>
                <h5>달리기</h5>
              </div>
            </v-list-item-content>
            <v-list-item-content>
              <div class="mx-auto text-center">
                <v-avatar color="thirdly" size="55" class="mb-2">
                  <span class="text-h5 font-weight-bold">80</span>
                </v-avatar>
                <h5>칼로리</h5>
              </div>
            </v-list-item-content>
            <v-list-item-content>
              <div class="mx-auto text-center">
                <v-avatar color="thirdly" size="55" class="mb-2">
                  <span class="text-h5 font-weight-bold">1</span>
                </v-avatar>
                <h5>낙상</h5>
              </div>
            </v-list-item-content>
          </v-list-item>
        </div>
      </v-list>
      <v-list class="border-style rounded-lg mt-1">
        <div outlined class="border-style-top rounded-t-lg">
          <div class="body-2 black--text ml-2 mt-2">밴드 정보</div>
          <v-list-item>
            <v-list-item-icon>
              <v-icon>
                mdi-watch-variant
              </v-icon>
            </v-list-item-icon>
            <v-list-item-content>
              0x00
            </v-list-item-content>
          </v-list-item>
        </div>
        <div class="border-style-top rounded-0">
          <div class="body-2 black--text ml-2 mt-2">개인 정보</div>
          <v-list-item>
            <v-list-item-icon>
              <v-icon>
                mdi-card-account-details
              </v-icon>
            </v-list-item-icon>
            <v-list-item-content>
              김갑생
            </v-list-item-content>
          </v-list-item>
          <v-list-item>
            <v-list-item-icon>
              <v-icon>
                mdi-calendar-today
              </v-icon>
            </v-list-item-icon>
            <v-list-item-content>
              1947년 09월 1일
            </v-list-item-content>
          </v-list-item>
        </div>
        <div class="border-style rounded-b-lg">
          <div class="body-2 black--text ml-2 mt-2">담당자</div>
          <v-list-item>
            <v-list-item-icon>
              <v-icon>
                mdi-account-tie
              </v-icon>
            </v-list-item-icon>
            <v-list-item-content>
              하재경
            </v-list-item-content>
            <v-list-item-action>
              <v-list-item-title>staff</v-list-item-title>
            </v-list-item-action>
          </v-list-item>
          <v-list-item>
            <v-list-item-icon>
              <v-icon>
                mdi-account-tie
              </v-icon>
            </v-list-item-icon>
            <v-list-item-content>
              김갑슨
            </v-list-item-content>
            <v-list-item-action>
              <v-list-item-title>manager</v-list-item-title>
            </v-list-item-action>
          </v-list-item>
        </div>
      </v-list>
    </v-container>
  </div>
</template>

<script>
export default {
  props: {
    bandInfo: {
      type: String,
      default: "",
    },
  },
  data: () => ({
    band: "",
  }),
  mounted() {
    this.changeJson();
  },
  created() {
    // this.check();
  },
  methods: {
    changeJson() {
      this.band = JSON.parse(this.bandInfo);
    },
  },
};
</script>
<style lang="scss">
.icon {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}
.border-style {
  border: 1px solid #d3d3d3;
}
.border-style-top {
  border-left: 1px solid #d3d3d3;
  border-right: 1px solid #d3d3d3;
  border-top: 1px solid #d3d3d3;
}
.border-style-bottom {
  border-left: 1px solid #d3d3d3;
  border-right: 1px solid #d3d3d3;
  border-bottom: 1px solid #d3d3d3;
}

.center {
  position: relative;
}
.v-icon {
  color: black;
}

v-icon {
  color: black;
}

#v-icon {
  color: black;
}
.band-name {
  font-size: 2.125rem;
  font-weight: bold;
  text-align: center;
}
</style>
